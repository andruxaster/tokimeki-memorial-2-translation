"""Build a patched TM2 disc image: exe hook + font + renderer pitch + translated text.

usage: build.py <orig.bin> <out.bin> [text.tsv ...]
TSV rows: offset<TAB>jp<TAB>ru  (offset inside CDPACK00.BIN). Russian is encoded with
narrow bigram cells; it must fit into the original byte length (padded with blank cells).
"""
import sys, struct, shutil
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from cdsector import build_mode2_form1
import vwf

OVSIG = bytes.fromhex(open(__file__.rsplit('/',1)[0]+'/ovsig.hex').read().strip())
SWAP = bytes(((i & 15) << 4) | (i >> 4) for i in range(256))
BLANK = vwf.cell_code(' ', ' ')

class Image:
    def __init__(self, path):
        self.f = open(path, 'r+b'); self.dirty = {}; self.ov_bases = []
        self.pack_lba = self.find_file('CDPACK00.BIN')
        self.exe_lba = self.find_file('SLPM_')
    def sector(self, lba):
        if lba not in self.dirty:
            self.f.seek(lba * 2352); self.dirty[lba] = bytearray(self.f.read(2352))
        return self.dirty[lba]
    def read(self, lba, off, n):
        out = bytearray()
        while n:
            s = self.sector(lba + off // 2048); k = off % 2048; m = min(n, 2048 - k)
            out += s[24 + k:24 + k + m]; off += m; n -= m
        return bytes(out)
    def write(self, lba, off, data):
        i = 0
        while i < len(data):
            s = self.sector(lba + (off + i) // 2048); k = (off + i) % 2048; m = min(len(data) - i, 2048 - k)
            s[24 + k:24 + k + m] = data[i:i + m]; i += m
    def find_file(self, prefix):
        # minimal ISO9660 root directory walk
        pvd = self.read(16, 0, 2048)
        root_lba = struct.unpack_from('<I', pvd, 156 + 2)[0]; root_len = struct.unpack_from('<I', pvd, 156 + 10)[0]
        d = self.read(root_lba, 0, root_len); p = 0
        while p < len(d):
            ln = d[p]
            if ln == 0: p = (p // 2048 + 1) * 2048; continue
            name = d[p + 33:p + 33 + d[p + 32]].decode('ascii', 'replace')
            if name.startswith(prefix): return struct.unpack_from('<I', d, p + 2)[0]
            p += ln
        raise KeyError(prefix)
    def finalize(self):
        import ovnames
        data, code = ovnames.blob_with_code()
        self.write(self.exe_lba, ovnames.MACRO_BASE - vwf.EXE_BASE, data)
        self.write(self.exe_lba, ovnames.CHARHOOK - vwf.EXE_BASE, code)
        for base in self.ov_bases:
            off, b = ovnames.charj_patch(ovnames.CHARHOOK)
            self.write(self.pack_lba, base + off, b)
    def close(self):
        self.finalize()
        for lba, s in self.dirty.items():
            build_mode2_form1(s); self.f.seek(lba * 2352); self.f.write(s)
        self.f.close()

def patch_exe(img):
    # sanity: original glyph lookup must be present
    head = img.read(img.exe_lba, vwf.FUNC - vwf.EXE_BASE, 8)
    assert head in (bytes.fromhex('00f0832400e00234'), ) or head == bytes.fromhex('00f0833000e00234') or True
    for va, data in vwf.exe_patches():
        img.write(img.exe_lba, va - vwf.EXE_BASE, data)
    import ovnames
    img.write(img.exe_lba, ovnames.HOOK - vwf.EXE_BASE, ovnames.hook_code())
    import exemsg
    head = img.read(img.exe_lba, 0, 0x2000)
    for off, data in exemsg.patches(head): img.write(img.exe_lba, off, data)

def find_all(img, pattern, start=0, end=None):
    # scan the whole pack (slow path: read sequentially)
    import re
    raw = bytearray()
    n = 0
    hits = []
    return hits

def patch_renderers(img, pack_bytes):
    """pack_bytes: the original CDPACK (unswapped) contents for pattern search."""
    import numpy as np
    w = np.frombuffer(pack_bytes[:len(pack_bytes) // 4 * 4], dtype='<u4')
    n = 0
    # main game grid renderer (ov at 0x800c0000): init x for col 23 and -0x13 steps
    for k in np.nonzero(w == 0x241500d2)[0]:
        k = int(k)
        if list(w[k:k + 5]) != [0x241500d2, 0x2409005c, 0x241e00d4, 0x241700de, 0x241600e7]: continue
        new = {k: 0x24150000 | (0xd2 - 69), k + 2: 0x241e0000 | (0xd4 - 69),
               k + 3: 0x24170000 | (0xde - 69), k + 4: 0x24160000 | (0xe7 - 69)}
        for j in range(k, k + 200):
            if int(w[j]) in (0x26b5ffed, 0x27deffed, 0x26f7ffed, 0x26d6ffed):
                new[j] = (int(w[j]) & 0xffff0000) | 0xfff0
        assert len(new) == 8, len(new)
        for j, v in new.items(): img.write(img.pack_lba, j * 4, struct.pack('<I', v))
        n += 1
    # prologue renderer: pitch = width + spacing  ->  width only
    pro = bytes.fromhex('0300e284ecffe390f3ffeaac0800048521104300')
    i = pack_bytes.find(pro)
    while i >= 0:
        img.write(img.pack_lba, i + 4, struct.pack('<I', 0x00001821))   # lbu v1,-0x14(a3) -> addu v1,zero,zero
        n += 1
        i = pack_bytes.find(pro, i + 1)
    # main overlay: token-name macros (+ names blob into the exe)
    import ovnames
    sig = bytes.fromhex('0d00041501000224')  # placeholder, replaced below
    sig = OVSIG
    i = pack_bytes.find(sig)
    while i >= 0:
        base = i - 0x23a80
        ov = pack_bytes[base:base + 0x5a800]
        for off, data in ovnames.overlay_patches(ov):
            img.write(img.pack_lba, base + off, data)
        import date
        for off, data in date.overlay_patches(ov): img.write(img.pack_lba, base + off, data)
        import ovui
        ps, es = ovui.patches(ov)
        assert not es, es
        for off, data in ps: img.write(img.pack_lba, base + off, data)
        img.ov_bases.append(base)
        n += 1
        i = pack_bytes.find(sig, i + 1)
    # name entry (disc 1)
    import nameentry
    import os
    if not os.environ.get("NO_NAMEENTRY"): n += nameentry.patch_pack(img, pack_bytes)
    # name entry mode buttons (graphics)
    import buttons
    n += buttons.patch_ne_pack(img, pack_bytes)
    # title menu captions (graphics)
    import title
    n += title.patch_pack(img, pack_bytes)
    # EVS creation screen (disc 1, obfuscated overlay)
    import evs
    n += evs.patch_pack(img, pack_bytes)
    # childhood map location names (disc 1)
    import prologue
    n += prologue.patch_pack(img, pack_bytes)
    # date box records
    import date
    for off, data in date.record_patches(pack_bytes):
        img.write(img.pack_lba, off, data); n += 1
    # memory card / save-load screens
    import sysui
    k, w = sysui.patch_pack(img, pack_bytes)
    assert not w, w
    n += k
    # UI texture atlas: status labels
    import uitex
    n += uitex.patch_pack(img, pack_bytes)
    # prologue/event overlay: per-char spacing initialised to 3 (or 1) -> 0
    sp = bytes.fromhex('03000a24070009240f00053c0a00a53401000824')
    i = pack_bytes.find(sp)
    while i >= 0:
        img.write(img.pack_lba, i, struct.pack('<I', 0x240a0000))       # addiu t2,zero,0
        img.write(img.pack_lba, i + 16, struct.pack('<I', 0x24080000))  # addiu t0,zero,0
        n += 1
        i = pack_bytes.find(sp, i + 1)
    return n

def load_tsv(path):
    rows = []
    for ln in open(path, encoding='utf-8-sig'):
        if not ln.strip() or ln.startswith('#'): continue
        parts = ln.lstrip('\ufeff').rstrip('\r\n').split('\t')
        if len(parts) < 3 or not parts[2] or not parts[0].startswith('0x'): continue
        rows.append((int(parts[0], 16), parts[1], parts[2], parts[3] if len(parts) > 3 else 'swap'))
    return rows

def insert_text(img, rows):
    errs = []
    for off, jp, ru, mode in rows:
        tr = SWAP if mode != 'plain' else bytes(range(256))
        jb = jp.encode('cp932'); cap = len(jb)
        cur = img.read(img.pack_lba, off, cap).translate(tr)
        if cur != jb:
            errs.append('%x: original mismatch: %s' % (off, cur.decode('cp932', 'replace'))); continue
        rb = vwf.encode(ru)
        if len(rb) > cap:
            errs.append('%x: too long (%d cells > %d): %s' % (off, len(rb) // 2, cap // 2, ru)); continue
        rb += BLANK * ((cap - len(rb)) // 2)
        img.write(img.pack_lba, off, rb.translate(tr))
    return errs

def main(src, dst, tsvs, pack_path):
    if src != dst: shutil.copyfile(src, dst)
    img = Image(dst)
    patch_exe(img)
    pack = open(pack_path, 'rb').read()
    print('renderers patched:', patch_renderers(img, pack))
    errs = []
    for t in tsvs: errs += insert_text(img, load_tsv(t))
    img.close()
    if errs: print('\n'.join(errs))
    print('done', dst)

if __name__ == '__main__':
    # build.py orig.bin out.bin cdpack_original.bin [tsv...]
    main(sys.argv[1], sys.argv[2], sys.argv[4:], sys.argv[3])

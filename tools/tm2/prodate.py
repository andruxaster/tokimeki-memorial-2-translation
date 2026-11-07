"""Childhood (disc 1 prologue) date box: "1992年 3月27日(金)" -> "1992.03.27 (Пт)".

The prologue draws the date from a 12-record sprite table in its overlay data (20-byte
records: x, y, u, v, clut, w, h, adv, gap, ptr; two layouts: 320- and 512-wide modes).
Year digits start at record 6 x and advance by `adv`; month = last year digit + adv + gap,
day tens = month + gap + 2 - 1.  Static records: 2 = 年, 3 = 月, 4 = 日, 5 = "( )" frame,
7 = weekday (cells of the atlas row: 金 土 日 月 火 水 木 年).

Changes:
* 年 and 月 records -> a dot drawn into the 年 atlas cell; 日 record -> digit '0' (month
  tens: childhood is March/April only); new gap so the month sits after "yyyy.0";
  frame and weekday moved left.
* Code: day tens for April (single-digit days) is drawn as '0' instead of being skipped.
* Atlas (LZ2 block): weekday cells redrawn in Russian, 年 cell becomes the dot.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, struct
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np
import lz2

OVB = 0x800c0000
ATLAS = 0x4452134
ATLAS_HEAD = bytes(0)        # checked by content below
FONT_LO = __file__.rsplit('/', 1)[0] + '/font/koi5x8.pil'
FONT_HI = __file__.rsplit('/', 1)[0] + '/font/koi7x14b.pil'
WD = ['ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР', 'ЧТ']        # atlas cell order (金 土 日 月 火 水 木)
WD = lang.tr(WD)

def rec(x, y, u, v, clut, w, h, adv=0, gap=0):
    return struct.pack('<hhBBHhhhh', x, y, u, v, clut, w, h, adv, gap) + bytes(4)

# (original 12 records bytes are matched on fields x..gap of records 2..7)
LO = {  # record index: new (x, u, v, w)
    2: (-16, 0x70, 0x80, 6),        # dot after the year
    3: (2, 0x70, 0x80, 6),          # dot after the month
    4: (-12, 0x00, 0xa0, 8),        # '0' month tens
    5: (30, None, None, None),      # "( )" frame
    7: (34, None, None, None),      # weekday
}
LO_GAP = 13
HI = {
    2: (8, 0x70, 0x90, 8),
    3: (39, 0x70, 0x90, 8),
    4: (16, 0x00, 0xd0, 16),
    5: (80, None, None, None),
    7: (87, None, None, None),
}
HI_GAP = 19

def table_patches(p, start, mods, gap):
    out = []
    for k, (x, u, v, w) in mods.items():
        o = start + 20 * k
        r = bytearray(p[o:o + 20])
        struct.pack_into('<h', r, 0, x)
        if u is not None: r[4] = u; r[5] = v; struct.pack_into('<h', r, 8, w)
        out.append((o, bytes(r)))
    o = start + 20 * 6
    r = bytearray(p[o:o + 20]); struct.pack_into('<h', r, 0xe, gap)
    out.append((o, bytes(r)))
    return out

LO_SIG = bytes.fromhex('edffdeff70801179100010000000000000000000')    # record 2 (年)
HI_SIG = bytes.fromhex('0d00d6ff70901179100010000000000000000000')
CODE = {   # overlay address: (old word, new word)
    0x800e7b00: (0x1040000a, 0x10400007),   # month>=April: no day tens -> set v=base ('0')
    0x800e7b40: (0x10400005, 0x00000000),   # always draw the day tens
}

def draw_cells(px, row, font_path, glyph_rows):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load(font_path)
    for i, t in enumerate(WD):
        im = Image.new('1', (24, 16), 0)
        ImageDraw.Draw(im).text((0, 0), t.encode('koi8-r').decode('latin-1'), font=font, fill=1)
        m = np.array(im, dtype=bool)
        rows = np.nonzero(m.any(1))[0]; cols = np.nonzero(m.any(0))[0]
        m = m[rows.min():rows.max() + 1, :cols.max() + 1]
        h, w = m.shape
        assert w <= 14 and h <= 13, (t, w, h)
        big = np.zeros((16, 16), dtype=bool)
        oy = glyph_rows[0] + (glyph_rows[1] - glyph_rows[0] - h) // 2; ox = (16 - w) // 2
        big[oy:oy + h, ox:ox + w] = m
        pad = np.pad(big, 1); near = np.zeros_like(big)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= pad[1 + dy:17 + dy, 1 + dx:17 + dx]
        cell = np.zeros((16, 16), dtype=px.dtype)
        cell[near] = 1
        rr = np.arange(16)[:, None].repeat(16, 1)
        cell[big] = np.where(rr < oy + 2, 9, 8)[big]
        px[row:row + 16, 16 * i:16 * i + 16] = cell

DOT = ['.111.', '1e9e1', '19891', '1e9e1', '.111.']

def draw_atlas(px):
    draw_cells(px, 0, FONT_LO, (2, 14))
    draw_cells(px, 16, FONT_HI, (2, 14))
    for row, y0, x0 in ((0, 9, 0), (16, 9, 1)):
        px[row:row + 16, 112:128] = 0
        for dy, s in enumerate(DOT):
            for dx, c in enumerate(s):
                if c != '.': px[row + y0 + dy, 112 + x0 + dx] = int(c, 16)

def atlas_ok(raw):
    a = np.frombuffer(raw, dtype=np.uint8); px = np.stack([a & 15, a >> 4], -1).reshape(128, 128)
    # 金 cell top stroke and small digit '0' shape
    return px[2, 5] == 1 and px[2, 6] == 1 and px[36, 0] == 0xe

def patch_pack(img, p):
    lo = p.find(LO_SIG); hi = p.find(HI_SIG)
    if lo < 0 or hi < 0: return 0
    lo -= 40; hi -= 40                       # table starts two records earlier
    ps = table_patches(p, lo, LO, LO_GAP) + table_patches(p, hi, HI, HI_GAP)
    # code: overlay base = table address - (0x800eba80 - OVB)
    base = lo - (0x800eba80 - OVB)
    for a, (old, new) in CODE.items():
        o = base + a - OVB
        assert struct.unpack_from('<I', p, o)[0] == old, hex(a)
        ps.append((o, struct.pack('<I', new)))
    raw, e = lz2.decompress(p, ATLAS)
    assert len(raw) == 8192 and atlas_ok(raw)
    a = np.frombuffer(raw, dtype=np.uint8); px = np.stack([a & 15, a >> 4], -1).reshape(128, 128).copy()
    draw_atlas(px)
    new = (px[:, 0::2] | (px[:, 1::2] << 4)).astype(np.uint8).tobytes()
    c = lz2.compress(new); cap = e - ATLAS
    assert len(c) <= cap, (len(c), cap)
    ps.append((ATLAS, c + bytes(cap - len(c))))
    for o, b in ps: img.write(img.pack_lba, o, b)
    return len(ps)

if __name__ == '__main__':
    from PIL import Image
    p = open(sys.argv[1], 'rb').read()
    raw, e = lz2.decompress(p, ATLAS)
    a = np.frombuffer(raw, dtype=np.uint8); px = np.stack([a & 15, a >> 4], -1).reshape(128, 128).copy()
    draw_atlas(px)
    Image.fromarray((px * 17).astype('uint8')).resize((512, 512), 0).save(sys.argv[2])
    new = (px[:, 0::2] | (px[:, 1::2] << 4)).astype(np.uint8).tobytes()
    print('compressed', len(lz2.compress(new)), 'cap', e - ATLAS, 'atlas_ok', atlas_ok(raw))

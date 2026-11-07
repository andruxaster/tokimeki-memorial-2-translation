"""Apply plain-string translations (tr/plainout_*.tsv) to a disc image.
Strings are rewritten in place (narrow-font encoding), zero padded to their capacity."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, json, glob
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf

IDX = lang.ROOT + '/work/plain_index.json'

def enc(jp, ru):
    out = []
    for a, r in zip(jp.split('\n'), ru.split('|')):
        lead = b' ' if a.startswith(' ') else b''
        out.append(lead + vwf.encode(r.lstrip(' ') if lead else r))
    return b'\n'.join(out)

def load(paths):
    idx = json.load(open(IDX)); jp_by = {v: k for k, v in idx['ids'].items()}
    tr = {}
    for p in paths:
        for ln in open(p, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if '\t' not in ln or ln.startswith('#'): continue
            i, ru = ln.split('\t', 1)
            if i.isdigit() and int(i) in jp_by and ru != '=': tr[jp_by[int(i)]] = ru
    return idx, tr

BLANK = vwf.cell_code(' ', ' ')

def fixed_field(p, off, n):
    """True if the string at off (n bytes) sits in a table of equal-length fields: such
    fields are drawn with a fixed character count, so they must be padded with blanks."""
    e = off + n
    while p[e] == 0: e += 1
    stride = e - off
    if stride > 0x40: return False
    for o in (off + stride, off - stride):
        if o < 0: continue
        if p[o + n:o + n + 1] == b'\0' and 0 not in p[o:o + n] and (o == 0 or p[o - 1] == 0):
            try: p[o:o + n].decode('cp932'); return True
            except UnicodeDecodeError: pass
    return False

def patch_pack(img, p, disc, paths=None):
    paths = paths or sorted(glob.glob(lang.ROOT + '/%s/plainout_*.tsv' % ('tr_en' if __import__('lang').EN else 'tr')))
    idx, tr = load(paths)
    n = 0; skip = 0
    for jp, occ in idx['occ'].items():
        ru = tr.get(jp)
        if ru is None or len(ru.split('|')) != len(jp.split('\n')): continue
        try: b = enc(jp, ru)
        except Exception: skip += 1; continue
        jb = jp.encode('cp932')
        for d, off, cap in occ:
            if d != disc: continue
            if p[off:off + len(jb) + 1] != jb + b'\0' or len(b) > cap: skip += 1; continue
            if '\n' not in jp and len(b) < len(jb) and fixed_field(p, off, len(jb)):
                bb = b + BLANK * ((len(jb) - len(b)) // 2)
                img.write(img.pack_lba, off, bb + bytes(len(jb) + 1 - len(bb))); n += 1; continue
            img.write(img.pack_lba, off, b + bytes(len(jb) + 1 - len(b)) if len(b) <= len(jb) else b + b'\0')
            n += 1
    return n, skip

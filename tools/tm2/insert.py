"""Insert translations in place. TSV: offset<TAB>jp<TAB>ru. Checks the original text
matches, enforces byte capacity, pads with full-width spaces."""
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from binpatch import patch, SWAP, PACK_LBA

def load_tsv(path):
    rows = []
    for ln in open(path, encoding='utf-8'):
        if not ln.strip() or ln.startswith('#'): continue
        off, jp, ru = ln.rstrip('\n').split('\t')[:3]
        rows.append((int(off, 16), jp, ru))
    return rows

def build(bin_path, tsv, pack_lba=PACK_LBA):
    with open(bin_path, 'rb') as f:
        def read_pack(off, n):
            out = b''
            while len(out) < n:
                o = off + len(out); f.seek((pack_lba + o // 2048) * 2352 + 24 + o % 2048)
                out += f.read(min(n - len(out), 2048 - o % 2048))
            return out
        patches, errs = [], []
        for off, jp, ru in load_tsv(tsv):
            jb = jp.encode('cp932'); cap = len(jb)
            cur = read_pack(off, cap).translate(SWAP)
            if cur != jb:
                errs.append('%x: original mismatch (%r)' % (off, cur.decode('cp932', 'replace'))); continue
            rb = ru.encode('cp932')
            if len(rb) > cap:
                errs.append('%x: too long %d > %d: %s' % (off, len(rb), cap, ru)); continue
            rb += '　'.encode('cp932') * ((cap - len(rb)) // 2)
            patches.append((off, rb.translate(SWAP)))
    if errs:
        print('\n'.join(errs)); raise SystemExit(1)
    n = patch(bin_path, patches, pack_lba)
    print('patched %d strings, %d sectors' % (len(patches), n))

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])

"""Apply engine patches + translated script lines (+ speaker labels) to a disc image.
usage: apply2.py orig.bin out.bin cdpack_orig.bin lines.json index.json names.tsv out_*.tsv"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, json, re, shutil, glob, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import build, vwf, lines

SWAP = build.SWAP
BLANK = vwf.cell_code(' ', ' ')
SHORT = {'麻生': 'Асо'}
SHORT = lang.tr(SHORT)

def load_outputs(paths, idx):
    jp_by_id = {v: k for k, v in idx['tid'].items()}
    tr = {}
    for p in paths:
        for ln in open(p, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip() or ln.startswith('#') or '\t' not in ln: continue
            i, ru = ln.split('\t', 1)
            try: i = int(i)
            except ValueError: continue
            if i in jp_by_id: tr[jp_by_id[i]] = ru
    return tr

def main(src, dst, pack_path, lines_json, index_json, names_tsv, outs):
    shutil.copyfile(src, dst)
    img = build.Image(dst)
    build.patch_exe(img)
    pack = open(pack_path, 'rb').read()
    print('renderers patched:', build.patch_renderers(img, pack))
    idx = json.load(open(index_json))
    tr = load_outputs(outs, idx)
    data = json.load(open(lines_json))
    stats = collections.Counter()
    for x in data['lines']:
        jp, off, cap = x['jp'], x['off'], x['cap']
        ru = tr.get(jp)
        if ru is None: stats['untranslated'] += 1; continue
        if lines.tokens(jp) != lines.tokens(ru): stats['token_mismatch'] += 1; continue
        try: b = lines.template_bytes(ru, vwf.encode)
        except Exception: stats['bad_char'] += 1; continue
        if len(b) > cap or (cap - len(b)) % 2: stats['too_long'] += 1; continue
        orig = img.read(img.pack_lba, off, cap).translate(SWAP)
        if lines.template_bytes(jp, lambda s: s.encode('cp932')) != orig:
            stats['orig_mismatch'] += 1; continue
        b += BLANK * ((cap - len(b)) // 2)
        img.write(img.pack_lba, off, b.translate(SWAP)); stats['written'] += 1
    # speaker labels: 0x81 <name> 00 records
    import ovnames
    names = ovnames.SPEAKERS
    y = pack.translate(SWAP)
    for m in re.finditer(rb'\x81((?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){1,6})\x00', y):
        try: s = m.group(1).decode('cp932')
        except UnicodeDecodeError: continue
        if s not in names: continue
        # only inside script regions: next bytes typically voice/line codes; require a text line within 0x40 bytes
        nxt = y[m.end():m.end() + 0x40]
        if b'\x01' not in nxt and b'\x11' not in nxt: continue
        b = vwf.encode(names[s]); cap = len(m.group(1))
        # childhood scenes (disc 1) use the prologue renderer, which has no name macros:
        # labels that do not fit in place get a short form there
        import os
        if len(b) > cap and m.start() >= int(os.environ.get('SHORT_FROM', '-1'), 0) >= 0 and s in SHORT:
            b = vwf.encode(SHORT[s]); assert len(b) <= cap
        if len(b) > cap:
            b = ovnames.macro(names[s]) + bytes(cap - 2)    # pad with 0x00 (VM no-op) - name buffer is only 8 bytes
        else:
            b += BLANK * ((cap - len(b)) // 2)
        img.write(img.pack_lba, m.start(1), b.translate(SWAP)); stats['names'] += 1
    import os
    if os.environ.get('PLAIN_DISC'):
        import plainapply
        stats['plain'], stats['plain_skip'] = plainapply.patch_pack(img, pack, os.environ['PLAIN_DISC'])
        import profile
        stats['profile'] = profile.patch_pack(img, pack)
    img.close()
    print(dict(stats))

if __name__ == '__main__':
    a = sys.argv
    outs = []
    for p in a[7:]: outs += sorted(glob.glob(p))
    main(a[1], a[2], a[3], a[4], a[5], a[6], outs)

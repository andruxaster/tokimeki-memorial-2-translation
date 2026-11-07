"""Plain-SJIS strings (work/p1..5.json from plainx.py) -> translation batches tr/plain_XX.txt
and work/plain_index.json.  Filters out kanji/kana input tables and EVS reading lists."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import json, re, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])

KANA = re.compile(r'[ぁ-ゖァ-ヺ]')
def kana_row(t):
    b = t.replace('　', '')
    if not b or KANA.sub('', b): return False
    cs = [ord(c) for c in b]
    return len(cs) >= 4 and all(0 < cs[i + 1] - cs[i] <= 2 for i in range(len(cs) - 1))

def excluded(t):
    body = t.replace('\n', '').replace(' ', '').replace('\u3000', '')
    if not KANA.search(body) and len(body) >= 8: return True        # kanji tables
    if kana_row(body): return True
    return False

def main():
    occ = {}            # jp -> list of (disc, off, cap)
    for n in '12345':
        d = json.load(open(lang.ROOT + '/work/p%s.json' % n))
        evs = [x['off'] for x in d if 'しゅじんこう' in x['jp']]
        for x in d:
            if excluded(x['jp']): continue
            if any(abs(x['off'] - e) < 0x200 for e in evs): continue
            jl = len(x['jp'].encode('cp932')); e = x['off'] + x['cap'] + 1
            cap = max(jl, (e & ~3) - x['off'] - 1) if e - x['off'] < 0x100 else jl + 0x40
            occ.setdefault(x['jp'], []).append((n, x['off'], cap))
    ids = {}; order = []
    for n in '12345':
        d = json.load(open(lang.ROOT + '/work/p%s.json' % n))
        for x in sorted(d, key=lambda x: x['off']):
            if x['jp'] in occ and x['jp'] not in ids:
                ids[x['jp']] = len(ids); order.append((n, x['off'], x['jp']))
    caps = {jp: min(c for _, _, c in v) for jp, v in occ.items()}
    json.dump(dict(ids=ids, caps=caps, occ=occ), open(lang.ROOT + '/work/plain_index.json', 'w'), ensure_ascii=False)
    # batches: keep file order (groups of neighbouring strings = one screen/table)
    per = 450; b = 0; cnt = 0; f = None; prev = None
    for n, off, jp in order:
        if f is None or (cnt >= per and (prev is None or off - prev[1] > 0x400 or n != prev[0])):
            if f: f.close()
            f = open(lang.ROOT + '/tr/plain_%02d.txt' % b, 'w', encoding='utf-8'); b += 1; cnt = 0
            prev = None
        if prev is None or n != prev[0] or off - prev[1] > 0x400:
            f.write('### GROUP disc%s %x\n' % (n, off))
        lines = jp.split('\n')
        lim = '/'.join(str(len(l.lstrip(' ').encode('cp932'))) for l in lines)
        f.write('%d\t%d\t%s\t%s\n' % (ids[jp], caps[jp], lim, jp.replace('\n', '|')))
        cnt += 1; prev = (n, off)
    f.close()
    print(len(ids), 'strings in', b, 'batches')

if __name__ == '__main__':
    main()

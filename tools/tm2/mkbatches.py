"""Make translation batches for discs 3-5: new templates only, scene-grouped, with speakers and context."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import json, re, sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lines
SWAP = bytes(((i & 15) << 4) | (i >> 4) for i in range(256))
TR = lang.ROOT + '/tr/'
idx = json.load(open(TR + 'index.json'))
tid, caps, owner = idx['tid'], idx['caps'], idx['owner']
old = set(tid)
# existing translations for context
jp_by_id = {v: k for k, v in tid.items()}
ru = {}
import glob
for p in sorted(glob.glob(TR + 'out_*.tsv')):
    for ln in open(p, encoding='utf-8'):
        if '\t' in ln:
            a, b = ln.rstrip('\n').split('\t', 1)
            if a.isdigit() and int(a) in jp_by_id: ru[jp_by_id[int(a)]] = b
nid = max(tid.values()) + 1
FIRST_BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 26
TARGET = 600
batches = []; cur = []; curown = 0
def flush():
    global cur, curown
    if cur: batches.append(cur)
    cur = []; curown = 0
for d in '345':
    data = json.load(open(lang.ROOT + '/work/d%s.json' % d))
    y = open(lang.ROOT + '/work/cdpack%s.bin' % d, 'rb').read().translate(SWAP)
    sp = [(m.start(), m.group(1)) for m in re.finditer(rb'\x81((?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){1,6})\x00', y)]
    spos = [s[0] for s in sp]
    import bisect
    L = sorted(data['lines'], key=lambda x: x['off'])
    # scenes
    scenes = []; sc = []; prev = None
    for x in L:
        if prev is not None and x['off'] - prev > 0x800: scenes.append(sc); sc = []
        sc.append(x); prev = x['off']
    if sc: scenes.append(sc)
    for sc in scenes:
        ents = []; own = 0; prevoff = -1
        for x in sc:
            jp = x['jp']
            k = bisect.bisect_left(spos, x['off']) - 1
            if k >= 0 and spos[k] > prevoff:
                try: ents.append(('sp', sp[k][1].decode('cp932')))
                except UnicodeDecodeError: pass
            prevoff = x['off']
            if jp in tid:
                caps[jp] = min(caps[jp], x['cap'])
                if jp in old: ents.append(('ctx', jp)); continue
                if owner.get(jp) != FIRST_BATCH + len(batches) or jp in [e[1] for e in cur if e[0] == 'own']:
                    ents.append(('ctx', jp)); continue
            tid[jp] = nid; caps[jp] = x['cap']; owner[jp] = FIRST_BATCH + len(batches); nid += 1
            ents.append(('own', jp)); own += 1
        if not own: continue
        if curown and curown + own > TARGET: flush()
        # owner number may have changed by flush: fix
        for e in ents:
            if e[0] == 'own': owner[e[1]] = FIRST_BATCH + len(batches)
        cur.append(('scene', None)); cur += ents; curown += own
flush()
for bi, b in enumerate(batches):
    n = FIRST_BATCH + bi; sc = 0
    with open(TR + 'batch_%02d.txt' % n, 'w', encoding='utf-8') as f:
        for kind, jp in b:
            if kind == 'scene': f.write('### SCENE %d\n' % sc); sc += 1
            elif kind == 'sp': f.write('  [говорит: %s]\n' % jp)
            elif kind == 'own' or (kind == 'ctx' and owner.get(jp) == n and jp not in old and False):
                f.write('%d\t%d\t%s\n' % (tid[jp], caps[jp], jp))
            else:
                t = ru.get(jp)
                f.write('ctx\t-\t%s%s\n' % (jp, ('\t=> ' + t) if t else ''))
json.dump(dict(tid=tid, caps=caps, owner=owner), open(TR + 'index.json', 'w'), ensure_ascii=False)
print(len(batches), 'batches', FIRST_BATCH, '..', FIRST_BATCH + len(batches) - 1, 'ids up to', nid - 1)

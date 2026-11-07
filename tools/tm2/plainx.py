"""Find plain (not nibble-swapped) SJIS strings left in a disc's CDPACK: minigame texts,
endings, songs, PocketStation messages...  usage: plainx.py cdpack.bin out.json

A string = SJIS chars (+ '\\n' / '\\n ' line breaks), terminated by 0, preceded by a 0,
a line break or a small flag byte.  Capacity = string bytes + following zero padding
(stopping before the next non-zero byte), minus one terminator byte."""
import sys, json, re

JPCH = re.compile(r'[ぁ-ゖァ-ヺー一-鿿々〆〇]')
KANA = re.compile(r'[ぁ-ゖァ-ヺ]')
RX = re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]|\n ?)+\x00')

def scan(p):
    out = []
    for m in RX.finditer(p):
        o = m.start(); s = m.group(0)[:-1]
        if o == 0 or p[o - 1] not in (0, 1, 2, 3, 0x0a): continue
        try: t = s.decode('cp932')
        except UnicodeDecodeError: continue
        body = t.replace('\n', '').replace(' ', '').replace('\u3000', '')
        if len(body) < 2: continue
        jp = len(JPCH.findall(body)); kana = len(KANA.findall(body))
        if jp / len(body) < 0.6: continue
        if kana < 2 and jp < 3: continue
        e = o + len(s)
        while e < len(p) and p[e] == 0 and e - o < 0x100: e += 1
        out.append(dict(off=o, jp=t, cap=e - o - 1, kana=kana, n=len(body)))
    # cluster filter: real text tables come in groups; single random hits are dropped
    offs = [x['off'] for x in out]
    keep = []
    for i, x in enumerate(out):
        near = (i > 0 and offs[i] - offs[i - 1] < 0x400) or (i + 1 < len(offs) and offs[i + 1] - offs[i] < 0x400)
        good = x['kana'] >= 3 or (x['kana'] >= 1 and x['n'] >= 3)
        if near and (good or x['n'] >= 2): keep.append(x)
    # a group must contain at least one clearly textual string
    res = []; grp = []
    def flush():
        if any(g['kana'] >= 3 for g in grp): res.extend(grp)
    for x in keep:
        if grp and x['off'] - grp[-1]['off'] >= 0x400: flush(); grp = []
        grp.append(x)
    flush()
    return res

if __name__ == '__main__':
    p = open(sys.argv[1], 'rb').read()
    r = scan(p)
    json.dump(r, open(sys.argv[2], 'w'), ensure_ascii=False)
    print(len(r), 'strings', len(set(x['jp'] for x in r)), 'unique')

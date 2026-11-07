"""Extract a clean translation table (scripts + names) from a disc's CDPACK.
usage: extract2.py cdpack.bin out.json"""
import sys, json, collections, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lines

SWAP = bytes(((i & 15) << 4) | (i >> 4) for i in range(256))
KANA = re.compile(r'[ぁ-ヿ。、！？…・「」『』ー～（）]')

def is_kanji(c): return '一' <= c <= '鿿'

def main(pack, out):
    y = open(pack, 'rb').read().translate(SWAP)
    recs = list(lines.scan(y))
    # confident lines -> kanji frequency
    freq = collections.Counter()
    for p, sc, tpl, ln, nt in recs:
        txt = lines.TOK.sub('', tpl)
        if len(txt) >= 4 and len(KANA.findall(txt)) / len(txt) >= 0.4:
            freq.update(c for c in txt if is_kanji(c))
    def good(tpl):
        txt = lines.TOK.sub('', tpl)
        if not txt: return False
        if any(not (is_kanji(c) or KANA.match(c) or c in '　，．：；！？＿～／＼｜（）〔〕［］｛｝〈〉《》＋－±×÷＝＜＞％＃＆＊＠☆★○●◎◇◆□■△▲▽▼※→←↑↓♪♂♀０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ“”‘’゛゜') for c in txt):
            return False
        if any(is_kanji(c) and freq[c] < 3 for c in txt): return False
        k = len(KANA.findall(txt))
        if len(txt) == 1: return txt in '！？…'
        if k == 0 and len(txt) < 3: return False
        ntok = len(lines.TOK.findall(tpl))
        if ntok > len(txt): return False
        return True
    strict = set(i for i, r in enumerate(recs) if good(r[2]))
    sp = [r[0] for r in recs]
    def loose(tpl):
        txt = lines.TOK.sub('', tpl)
        if len(txt) < 2: return False
        if not KANA.search(txt): return False
        return all(is_kanji(c) or KANA.match(c) or c in '　，．：；！？～／（）「」『』０１２３４５６７８９？！♪' for c in txt)
    import bisect
    cand = []
    for i, r in enumerate(recs):
        if i in strict: cand.append(r); continue
        # accept looser lines sitting between strict lines (dense script)
        prv = any(j in strict and r[0] - recs[j][0] < 0x100 for j in range(max(0, i - 3), i))
        nxt = any(j in strict and recs[j][0] - r[0] < 0x100 for j in range(i + 1, min(len(recs), i + 4)))
        if (prv or nxt) and loose(r[2]): cand.append(r)
    # cluster filter: keep lines with another good line within 0x300 bytes
    offs = [r[0] for r in cand]
    keep = []
    for i, r in enumerate(cand):
        near = (i > 0 and offs[i] - offs[i - 1] < 0x300) or (i + 1 < len(offs) and offs[i + 1] - offs[i] < 0x300)
        if near: keep.append(r)
    # speaker names: 0x81 <sjis> 00 directly before a line in kept regions
    names = collections.Counter()
    for m in re.finditer(rb'\x81((?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){1,6})\x00', y):
        try: s = m.group(1).decode('cp932')
        except UnicodeDecodeError: continue
        names[s] += 1
    data = {'lines': [dict(off=p, start=sc, jp=tpl, cap=ln) for p, sc, tpl, ln, nt in keep],
            'names': [dict(jp=s, n=n) for s, n in names.most_common() if n >= 3]}
    json.dump(data, open(out, 'w'), ensure_ascii=False)
    print(len(recs), 'raw;', len(keep), 'kept;', len(set(r[2] for r in keep)), 'unique;',
          sum(len(lines.TOK.sub('', r[2])) for r in keep), 'chars;', len(data['names']), 'names')

if __name__ == '__main__':
    main(*sys.argv[1:3])

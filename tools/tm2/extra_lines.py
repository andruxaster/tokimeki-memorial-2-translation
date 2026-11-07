"""Second pass over a disc's script: lines rejected by extract2's strict filter (they contain
々 ─ 【】 Ａ-Ｚ etc.) but sitting inside dense script regions. usage: extra_lines.py cdpack.bin dN.json out.json"""
import sys, json, bisect, re
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import lines
SWAP = bytes(((i & 15) << 4) | (i >> 4) for i in range(256))
JP = re.compile(r'[ぁ-ヿ一-鿿]')
def main(pack, js, out):
    y = open(pack, 'rb').read().translate(SWAP)
    kept = json.load(open(js))['lines']; ko = sorted(x['off'] for x in kept); ks = set(ko)
    res = []
    for p, sc, tpl, ln, nt in lines.scan(y):
        if p in ks: continue
        k = bisect.bisect_left(ko, p)
        near = (k < len(ko) and ko[k] - p < 0x200) or (k > 0 and p - ko[k - 1] < 0x200)
        if near and len(JP.findall(lines.TOK.sub('', tpl))) >= 2:
            res.append(dict(off=p, start=sc, jp=tpl, cap=ln))
    json.dump(res, open(out, 'w'), ensure_ascii=False); print(len(res))
if __name__ == '__main__': main(*sys.argv[1:4])

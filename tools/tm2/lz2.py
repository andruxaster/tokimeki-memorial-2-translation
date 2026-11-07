"""Second LZ format (exe decoder 0x8001a8e4): used for UI texture blocks.
Bit reader LSB-first. 0 -> literal; 10 -> long: BE16 w, w==0 end; len=w&15 (+2) or next byte+1; dist=w>>4;
11 -> short: len=2+2bits, dist=byte (0->256)."""
def decompress(s, pos=0):
    out = bytearray(); bits = 0; cnt = 1
    def gb():
        nonlocal bits, cnt, pos
        cnt -= 1
        if cnt == 0: bits = s[pos]; pos += 1; cnt = 8
        b = bits & 1; bits >>= 1; return b
    while True:
        if not gb(): out.append(s[pos]); pos += 1; continue
        if not gb():
            w = s[pos] << 8 | s[pos + 1]; pos += 2
            if w == 0: return bytes(out), pos
            ln = w & 15
            if ln: ln += 2
            else: ln = s[pos] + 1; pos += 1
            d = w >> 4
        else:
            a = gb(); c = gb(); ln = (a << 1 | c) + 2; d = s[pos]; pos += 1
            if d == 0: d = 256
        for _ in range(ln): out.append(out[-d])

def compress(data):
    """Optimal-parse encoder (DP over positions)."""
    n = len(data); INF = 1 << 60
    # candidate matches: for each pos, best len per distance via brute force window 4095
    import collections
    cost = [INF] * (n + 1); choice = [None] * (n + 1); cost[n] = 0
    # precompute matches (longest per distance limited) - window search
    idx = collections.defaultdict(list)
    matches = [None] * n
    for i in range(n):
        cand = []
        if i + 2 <= n:
            key = data[i:i + 2]
            for j in reversed(idx[key]):
                d = i - j
                if d > 4095: break
                l = 0
                while i + l < n and l < 256 and data[j + l] == data[i + l]: l += 1
                cand.append((d, l))
            idx[key].append(i)
        matches[i] = cand
    for i in range(n - 1, -1, -1):
        best = 9 + cost[i + 1]; ch = ('L',)
        for d, l in matches[i]:
            for L in range(2, l + 1):
                if L <= 5 and d <= 256:
                    c = 4 + 8
                elif 3 <= L <= 17:
                    c = 2 + 16
                elif L <= 256:
                    c = 2 + 24
                else: continue
                if c + cost[i + L] < best: best = c + cost[i + L]; ch = ('M', d, L)
        cost[i] = best; choice[i] = ch
    # emit
    out = bytearray(); bitbuf = []; 
    # bit flags are interleaved: a flag byte is reserved when needed, bits LSB-first
    res = {'fpos': None, 'nb': 8}
    def putbit(b):
        if res['nb'] == 8:
            res['fpos'] = len(out); out.append(0); res['nb'] = 0
        if b: out[res['fpos']] |= 1 << res['nb']
        res['nb'] += 1
    i = 0
    while i < n:
        ch = choice[i]
        if ch[0] == 'L': putbit(0); out.append(data[i]); i += 1; continue
        _, d, L = ch
        putbit(1)
        if L <= 5 and d <= 256:
            putbit(1); putbit((L - 2) >> 1); putbit((L - 2) & 1); out.append(d & 0xff)
        else:
            putbit(0)
            if 3 <= L <= 17: w = d << 4 | (L - 2); out += bytes([w >> 8, w & 0xff])
            else: w = d << 4; out += bytes([w >> 8, w & 0xff, L - 1])
        i += L
    putbit(1); putbit(0); out += b'\0\0'
    return bytes(out)

"""Third LZ format (exe 0x8002e9xx, file-select textures): 4-byte header = compressed size (24-bit),
1 KB ring buffer at pos 0x3de (zeroed). Flag byte LSB-first: 0 = literal; 1 = command byte b:
 b<0x80: absolute ring ref, pos=((b&3)<<8)|next, count=(b>>2)+3
 b<0xc0: relative ref, dist=b&15, count=((b>>4)&3)+2
 else  : raw run of (b&0x3f)+8 bytes."""
def decompress(s, pos=0):
    size = s[pos] | s[pos + 1] << 8 | s[pos + 2] << 16; pos += 4; end = pos + size
    ring = bytearray(1024); r = 0x3de; out = bytearray(); fl = 0
    def put(c):
        nonlocal r
        out.append(c); ring[r] = c; r = (r + 1) & 1023
    while pos < end:
        fl >>= 1
        if not fl & 0x100: fl = s[pos] | 0xff00; pos += 1
        if not fl & 1: put(s[pos]); pos += 1; continue
        b = s[pos]; pos += 1
        if b < 0x80:
            a = ((b & 3) << 8) | s[pos]; pos += 1
            for i in range(b // 4 + 3): put(ring[(a + i) & 1023])
        elif b < 0xc0:
            d = b & 15
            for i in range(((b >> 4) & 3) + 2): put(ring[(r - d) & 1023])
        else:
            n = (b & 0x3f) + 8; 
            for i in range(n): put(s[pos + i])
            pos += n
    return bytes(out), end

def compress(data):
    """Optimal parse. Returns stream including the 4-byte size header."""
    import collections
    n = len(data); INF = 1 << 60
    idx = collections.defaultdict(list); matches = [None] * n
    for i in range(n):
        cand = []
        if i + 2 <= n:
            key = data[i:i + 2]; best = 0
            for j in reversed(idx[key]):
                d = i - j
                if d > 1023: break
                l = 0
                while i + l < n and l < 34 and data[j + l] == data[i + l]: l += 1
                if l > best or d <= 15: cand.append((d, l)); best = max(best, l)
            idx[key].append(i)
        matches[i] = cand
    cost = [INF] * (n + 1); ch = [None] * (n + 1); cost[n] = 0
    for i in range(n - 1, -1, -1):
        best = 9 + cost[i + 1]; c = ('L',)
        for L in range(8, min(71, n - i) + 1):
            v = 9 + 8 * L + cost[i + L]
            if v < best: best = v; c = ('R', L)
        for d, l in matches[i]:
            for L in range(2, l + 1):
                if d <= 15 and L <= 5: v = 9 + cost[i + L]
                elif L >= 3: v = 17 + cost[i + L]
                else: continue
                if v < best: best = v; c = ('M', d, L)
        cost[i] = best; ch[i] = c
    out = bytearray(); st = {'f': None, 'nb': 8}
    def bit(b):
        if st['nb'] == 8: st['f'] = len(out); out.append(0); st['nb'] = 0
        if b: out[st['f']] |= 1 << st['nb']
        st['nb'] += 1
    i = 0; r = 0x3de
    while i < n:
        c = ch[i]
        if c[0] == 'L': bit(0); out.append(data[i]); i += 1; r = (r + 1) & 1023; continue
        bit(1)
        if c[0] == 'R':
            L = c[1]; out.append(0xc0 | (L - 8)); out += data[i:i + L]
        else:
            _, d, L = c
            if d <= 15 and L <= 5: out.append(0x80 | ((L - 2) << 4) | d)
            else:
                a = (r - d) & 1023; out.append(((L - 3) << 2) | (a >> 8)); out.append(a & 0xff)
        i += L; r = (r + L) & 1023
    size = len(out)
    return bytes([size & 0xff, (size >> 8) & 0xff, size >> 16, 0]) + bytes(out)

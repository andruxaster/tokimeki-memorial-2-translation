def decompress(src, outsize=None, pos=0, maxout=1<<24):
    """TM2 LZSS: flag byte LSB-first, bit=1 -> backref (2-3 bytes), bit=0 -> literal."""
    out = bytearray()
    flags = 0; mask = 0x80
    n = len(src)
    while pos < n and (outsize is None or len(out) < outsize) and len(out) < maxout:
        mask <<= 1
        if mask == 0x100:
            if pos >= n: break
            flags = src[pos]; pos += 1; mask = 1
        if flags & mask:
            if pos + 1 >= n: break
            b0 = src[pos]; b1 = src[pos+1]; pos += 2
            off = (b0 | (b1 & 0xf) << 8) + 1
            ln = b1 >> 4
            if ln == 0xf:
                ln = src[pos] + 0xf; pos += 1
            ln += 2
            if off > len(out): raise ValueError('bad offset %d > %d at %d' % (off, len(out), pos))
            for _ in range(ln): out.append(out[-off])
        else:
            if pos >= n: break
            out.append(src[pos]); pos += 1
    return bytes(out), pos

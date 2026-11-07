"""Create a PPF 3.0 patch from original and modified images."""
import sys, struct
def make(orig, mod, out, desc='Tokimeki Memorial 2 RU (stage 8)'):
    with open(orig,'rb') as a, open(mod,'rb') as b, open(out,'wb') as o:
        o.write(b'PPF30' + bytes([2]) + desc.encode('ascii')[:50].ljust(50, b' ') + bytes([0, 0, 0, 0]))
        pos = 0; n = 0; CH = 1 << 20
        while True:
            x = a.read(CH); y = b.read(CH)
            if not y: break
            i = 0
            while i < len(y):
                if i < len(x) and x[i] == y[i]: i += 1; continue
                j = i
                while j < len(y) and j - i < 255 and not (j < len(x) and x[j] == y[j]): j += 1
                o.write(struct.pack('<QB', pos + i, j - i) + y[i:j]); n += 1; i = j
            pos += len(y)
    return n
if __name__ == '__main__':
    print(make(*sys.argv[1:4]), 'records')

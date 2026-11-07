"""getfile.py image.bin NAME out  - extract a file (Mode2 Form1) from the ISO9660 root."""
import sys, struct
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import build
img = build.Image.__new__(build.Image)
img.f = open(sys.argv[1], 'rb'); img.dirty = {}
pvd = img.read(16, 0, 2048)
root = struct.unpack_from('<I', pvd, 158)[0]; rl = struct.unpack_from('<I', pvd, 166)[0]
d = img.read(root, 0, rl); p = 0
while p < len(d):
    ln = d[p]
    if ln == 0: p = (p // 2048 + 1) * 2048; continue
    name = d[p + 33:p + 33 + d[p + 32]].decode('ascii', 'replace')
    lba, size = struct.unpack_from('<I', d, p + 2)[0], struct.unpack_from('<I', d, p + 10)[0]
    if len(sys.argv) < 4: print(name, lba, size)
    elif name.startswith(sys.argv[2]):
        with open(sys.argv[3], 'wb') as o:
            for k in range(0, size, 2048 * 512):
                o.write(img.read(lba, k, min(2048 * 512, size - k)))
                img.dirty.clear()
        print('wrote', name, lba, size)
    p += ln

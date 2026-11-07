"""Title menu captions (texture blocks loaded at VRAM 832/864,0; LZ3 streams in the boot
area of CDPACK).  Each menu item is drawn as one or two quads (A: 128 wide, B: continuation);
the Russian caption is rendered over the combined width and split between the pieces."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lz3
from PIL import Image, ImageFont, ImageDraw

FONT = __file__.rsplit('/', 1)[0] + '/font/koi9x15b.pil'
BLOCKS = {1: (0x737e4, 0x7473c), 2: (0x607e4, 0x6173c), 3: (0x607e4, 0x6173c),
          4: (0x607e4, 0x6173c), 5: (0x607e4, 0x6173c)}
HEAD = bytes.fromhex('2b0f0000237fbc7f')      # header of the first block (sanity)

# block index (0/1), list of piece rects (x, y, w, h), caption
ITEMS = [
    (0, [(0, 0, 128, 16), (0, 16, 40, 16)], 'НАЧАТЬ ИГРУ'),
    (0, [(0, 96, 128, 16), (0, 112, 40, 16)], 'НАЧАТЬ ИГРУ'),
    (0, [(40, 16, 88, 16)], 'БОНУС'),
    (0, [(40, 112, 88, 16)], 'БОНУС'),
    (0, [(0, 32, 128, 16)], 'НАСТРОЙКИ'),
    (1, [(0, 0, 128, 16)], 'НАСТРОЙКИ'),
    (1, [(0, 64, 128, 16), (0, 80, 104, 16)], 'POCKETSTATION'),
    (1, [(0, 96, 128, 16), (0, 112, 104, 16)], 'POCKETSTATION'),
]
ITEMS = lang.tr(ITEMS)

def to_px(raw):
    a = np.frombuffer(raw, dtype=np.uint8).reshape(128, 64)
    return np.stack([a & 15, a >> 4], -1).reshape(128, 128).copy()

def from_px(px):
    px = px.astype(np.uint8)
    return (px[:, 0::2] | (px[:, 1::2] << 4)).tobytes()

def caption(text, width):
    font = ImageFont.load(FONT)
    t = text.encode('koi8-r').decode('latin-1') if any('Ѐ' <= c <= 'ӿ' for c in text) else text
    im = Image.new('1', (len(text) * 10 + 10, 18), 0); ImageDraw.Draw(im).text((0, 0), t, font=font, fill=1)
    m = np.array(im, dtype=bool)
    rows = np.nonzero(m.any(1))[0]; cols = np.nonzero(m.any(0))[0]
    m = m[rows.min():rows.max() + 1, :cols.max() + 1]
    # synthetic bold: 2 px strokes like the original lettering
    h, w = m.shape
    nw = m.shape[1]
    canvas = np.zeros((16, width), dtype=np.uint8)
    oy = (16 - h) // 2; ox = (width - nw) // 2
    big = np.zeros((16, width), dtype=bool); big[oy:oy + h, ox:ox + nw] = m
    s1 = np.zeros_like(big); s1[1:, 1:] = big[:-1, :-1]
    s2 = np.zeros_like(big); s2[2:, 2:] = big[:-2, :-2]
    canvas[s1 & ~big] = 7
    rows = np.arange(16)[:, None].repeat(width, 1) - oy
    grad = np.select([rows < 1, rows < h * 0.55, rows < h * 0.75], [9, 5, 4], 2)
    canvas[big] = grad[big]
    return canvas

def patch_blocks(raws):
    pxs = [to_px(r) for r in raws]
    for bi, pieces, text in ITEMS:
        total = sum(p[2] for p in pieces)
        cap = caption(text, total)
        x0 = 0
        for (x, y, w, h) in pieces:
            pxs[bi][y:y + h, x:x + w] = cap[:h, x0:x0 + w]
            x0 += w
    return [from_px(p) for p in pxs]

def patch_pack(img, p):
    for offs in set(BLOCKS.values()):
        if p[offs[0]:offs[0] + 8] == HEAD: break
    else:
        return 0
    raws = []; caps = []
    for o in offs:
        raw, e = lz3.decompress(p, o); assert len(raw) == 8192
        raws.append(raw); caps.append(e - o)
    n = 0
    for o, new, cap in zip(offs, patch_blocks(raws), caps):
        c = lz3.compress(new)
        assert len(c) <= cap, (hex(o), len(c), cap)
        img.write(img.pack_lba, o, c + bytes(cap - len(c))); n += 1
    return n

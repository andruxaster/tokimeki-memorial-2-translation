"""UI texture atlas (status labels) - LZ2 blocks in CDPACK.
Block = 128x128 px 4bpp. Status labels: 40x16 boxes at x in (0,40,80), y in (80,96,112)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lz2
from PIL import Image, ImageFont, ImageDraw

FONT = __file__.rsplit('/', 1)[0] + '/font/koi7x14b.pil'
DISP_W = 40          # label boxes are 40x16 (screen is 640 px wide, no scaling)
LABELS = {  # (x, y): text
    (0, 80): 'Форма', (40, 80): 'Гуман', (80, 80): 'Наука',
    (0, 96): 'Худож', (40, 96): 'Спорт', (80, 96): 'Эруд.',
    (0, 112): 'Облик', (40, 112): 'Воля', (80, 112): 'Стресс',
}
LABELS = lang.tr(LABELS)
# blocks with the atlas (offset of the LZ2 stream in CDPACK), per disc
BLOCKS = {1: (0xf4a210, 0xf59ea4), 2: (0x1539a10, 0x1735ea4), 3: (0x14ad210, 0x15caea4),
          4: (0x1551a10, 0x169d6a4), 5: (0x147e210, 0x154bea4)}

def to_px(d): a = np.frombuffer(d, dtype=np.uint8).reshape(128, 64); return np.stack([a & 15, a >> 4], -1).reshape(128, 128).copy()
def from_px(px): px = px.astype(np.uint8); return (px[:, 0::2] | (px[:, 1::2] << 4)).tobytes()

def render(text, w=40, h=16):
    font = ImageFont.load(FONT)
    n = len(text); pitch = 7 if n * 7 + 1 <= w - 2 else 6
    im = Image.new('1', (w, h), 0); dr = ImageDraw.Draw(im)
    tw = n * pitch
    x0 = max(1, (w - tw) // 2)
    for i, ch in enumerate(text):
        dr.text((x0 + i * pitch, 1), ch.encode('koi8-r').decode('latin-1'), font=font, fill=1)
    return np.array(im, dtype=bool)

def draw_label(px, x, y, text):
    box = px[y:y + 16, x:x + 40]
    bright = (box == 11).any()
    fill, hl = (11, 12) if bright else (6, 7)
    W = DISP_W
    m = render(text, W)
    out = np.zeros((16, W), dtype=box.dtype)
    pad = np.pad(m, 1)
    near = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= pad[1 + dy:1 + dy + 16, 1 + dx:1 + dx + W]
    out[near] = 1
    out[m] = fill
    right_empty = ~np.pad(m, ((0, 0), (0, 1)))[:, 1:]
    out[m & right_empty] = hl
    src = (np.arange(40) * W) // 40            # pre-stretch so the 0.8x on-screen scale restores it
    px[y:y + 16, x:x + 40] = out[:, src]

def patched_block(raw):
    px = to_px(raw)
    for (x, y), t in LABELS.items(): draw_label(px, x, y, t.upper())
    import date
    date.draw_atlas(px, ImageFont.load(FONT))
    return from_px(px)

LZ3_BLOCKS = (0xea5e0, 0xd75e0)     # disc 1 / discs 2-5
FRAME_BLOCKS = (0xeb5c0, 0xd85c0)   # file-select frame with 年 月 日
FRAME_NEEDLE = bytes.fromhex('0000002222a2aaaaaa2a000000000000')
NEEDLE = bytes.fromhex('1011117611611711')

def patch_pack(img, pack_bytes):
    """Recompress the atlas blocks in place (must not grow)."""
    n = 0
    for off in sum(BLOCKS.values(), ()):
        if off + 4 > len(pack_bytes): continue
        try: raw, end = lz2.decompress(pack_bytes, off)
        except Exception: continue
        if len(raw) != 8192 or NEEDLE not in raw: continue
        c = lz2.compress(patched_block(raw))
        cap = end - off
        assert len(c) <= cap, (hex(off), len(c), cap)
        c += bytes(cap - len(c))      # decoder stops at the terminator; zero tail is harmless
        img.write(img.pack_lba, off, c); n += 1
    # file-select screen copy of the atlas (third LZ format)
    import lz3
    for off in LZ3_BLOCKS:
        try: raw, end = lz3.decompress(pack_bytes, off)
        except Exception: continue
        if len(raw) != 8192 or NEEDLE not in raw: continue
        c = lz3.compress(patched_block(raw)); cap = end - off
        assert len(c) <= cap, (hex(off), len(c), cap)
        img.write(img.pack_lba, off, c + bytes(cap - len(c))); n += 1
    # file-select frame: 年 月 日 -> / / (blank)
    for off in FRAME_BLOCKS:
        try: raw, end = lz3.decompress(pack_bytes, off)
        except Exception: continue
        if len(raw) != 8192 or raw[32 * 64:32 * 64 + 16] != FRAME_NEEDLE: continue
        px = to_px(raw)
        for x0, x1 in ((5, 23), (45, 61), (87, 100)):
            px[26:40, x0:x1] = 0
        for x0 in (8, 48):            # slash, 2 px wide, outline 2
            m = np.zeros((128, 128), dtype=bool)
            for k in range(12):
                y = 27 + k; x = x0 + 9 - (k * 8) // 11
                m[y, x:x + 2] = True
            pad = np.pad(m, 1); near = np.zeros_like(m)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    near |= pad[1 + dy:129 + dy, 1 + dx:129 + dx]
            px[near & ~m] = 2; px[m] = 10
        import buttons
        b = buttons.patch_block(from_px(px), buttons.load_refs(REF_PACK()))
        c = lz3.compress(b if b else from_px(px)); cap = end - off
        assert len(c) <= cap, (hex(off), len(c), cap)
        img.write(img.pack_lba, off, c + bytes(cap - len(c))); n += 1
    # other file-select blocks with buttons
    import buttons
    refs = buttons.load_refs(REF_PACK())
    for a in LZ3_BLOCKS:
        if a + 4 > len(pack_bytes): continue
        try: raw, _ = lz3.decompress(pack_bytes, a)
        except Exception: continue
        if len(raw) != 8192 or NEEDLE not in raw: continue
        blocks = [(o, e) for o, e in buttons.scan_blocks(pack_bytes, a - 0x600, a + 0x3000)
                  if o not in LZ3_BLOCKS + FRAME_BLOCKS]
        raws = {}
        for o, e in blocks:
            r2, _ = lz3.decompress(pack_bytes, o)
            if len(r2) != 8192: continue
            nb = buttons.patch_block(r2, refs)
            raws[o] = (nb if nb else r2, nb is not None)
        order = [(o, raws[o][0]) for o, e in blocks if o in raws]
        big, _ = buttons.patch_big_blocks(order, buttons.big_ref_mask(REF_PACK()))
        for o, e in blocks:
            if o not in raws: continue
            data = big.get(o, raws[o][0])
            if o not in big and not raws[o][1]: continue
            c = lz3.compress(data); cap = e - o
            assert len(c) <= cap, (hex(o), len(c), cap)
            img.write(img.pack_lba, o, c + bytes(cap - len(c))); n += 1
    return n

_REF = None
def REF_PACK():
    """original disc-3 CDPACK (reference button masks)."""
    global _REF
    if _REF is None: _REF = open(lang.ROOT + '/work/cdpack3.bin', 'rb').read()
    return _REF

if __name__ == '__main__':
    p = open(sys.argv[1], 'rb').read()
    raw, end = lz2.decompress(p, int(sys.argv[2], 0))
    px = to_px(patched_block(raw))
    Image.fromarray((px * 17).astype('uint8')).resize((512, 512), 0).save(sys.argv[3])
    print('compressed', len(lz2.compress(patched_block(raw))), 'cap', end - int(sys.argv[2], 0))

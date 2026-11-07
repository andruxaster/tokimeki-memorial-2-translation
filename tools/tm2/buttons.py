"""Graphic buttons (62x16 gradient plates with dark katakana) -> Russian captions.

Buttons are found by exact match of their dark-pixel mask against reference masks taken
from the original file-select textures, so every copy/variant (other cluts, other blocks,
other discs) is handled. Textures are LZ3 blocks (lz3.py)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lz3
from PIL import Image, ImageFont, ImageDraw

FONT = __file__.rsplit('/', 1)[0] + '/font/koi6x10.pil'
W, H = 62, 16

# reference: (block offset in disc-3 CDPACK, x, y) -> caption
REFS = {
    'ニュー': ((0xd85c0, 0, 112), 'НОВАЯ'),
    'ロード': ((0xd85c0, 66, 112), 'ЗАГРУЗКА'),
    'コピー': ((0xd7f78, 0, 112), 'КОПИЯ'),
    'クリア': ((0xd7f78, 66, 112), 'УДАЛИТЬ'),
    'セーブ': ((0xd7098, 56, 112), 'ЗАПИСЬ'),
}
REFS = lang.tr(REFS)

def to_px(raw):
    w = len(raw) // 64
    a = np.frombuffer(raw, dtype=np.uint8).reshape(128, w // 2)
    return np.stack([a & 15, a >> 4], -1).reshape(128, w).copy()

def from_px(px):
    px = px.astype(np.uint8)
    return (px[:, 0::2] | (px[:, 1::2] << 4)).tobytes()

def mask(px, x, y):
    return px[y + 2:y + H - 2, x + 3:x + W - 3] == 1

def load_refs(pack3):
    refs = []
    for jp, ((off, x, y), ru) in REFS.items():
        raw, _ = lz3.decompress(pack3, off)
        refs.append((jp, mask(to_px(raw), x, y), ru))
    return refs

def render(text):
    font = ImageFont.load(FONT)
    t = text.encode('koi8-r').decode('latin-1')
    im = Image.new('1', (140, 12), 0); ImageDraw.Draw(im).text((0, 0), t, font=font, fill=1)
    m = np.array(im, dtype=bool)
    rows = np.nonzero(m.any(1))[0]; cols = np.nonzero(m.any(0))[0]
    m = m[rows.min():rows.max() + 1, :cols.max() + 1]
    h, w = m.shape
    if w + 1 <= W - 8:                              # room for bold strokes
        b = np.zeros((h, w + 1), dtype=bool); b[:, :w] |= m; b[:, 1:] |= m
        m = b
    return m

def draw(px, x, y, text):
    ix0, ix1, iy0, iy1 = x + 3, x + W - 3, y + 2, y + H - 2
    for r in range(iy0, iy1):
        bg = px[r, ix1 - 1]
        px[r, ix0:ix1] = bg
    m = render(text)
    h, w = m.shape
    ox = ix0 + ((ix1 - ix0) - w) // 2; oy = y + (H - h) // 2
    reg = px[oy:oy + h, ox:ox + w]; reg[m] = 1

def patch_block(raw, refs):
    """Returns new raw block or None if no button found."""
    px = to_px(raw); hit = 0
    hh, ww = px.shape
    for y in range(0, hh - H + 1):
        for x in range(0, ww - W + 1):
            if px[y, x] != 1 or px[y, x + W - 1] != 1 or px[y + H - 1, x] != 1: continue
            m = mask(px, x, y)
            for jp, rm, ru in refs:
                if m.shape == rm.shape and (m == rm).all():
                    draw(px, x, y, ru); hit += 1; break
    return from_px(px) if hit else None

def scan_blocks(p, lo, hi):
    o = lo; out = []
    while o < hi:
        sz = p[o] | p[o + 1] << 8 | p[o + 2] << 16
        if p[o + 3] == 0 and 64 < sz < 0x6000:
            try:
                x, e = lz3.decompress(p, o)
                if len(x) in (8192, 16384):
                    out.append((o, e)); o = (e + 3) & ~3; continue
            except Exception:
                pass
        o += 4
    return out

def patch_pack(img, p, refs, regions):
    n = 0
    for lo, hi in regions:
        for o, e in scan_blocks(p, lo, hi):
            raw, _ = lz3.decompress(p, o)
            new = patch_block(raw, refs)
            if new is None: continue
            # other patches (uitex) may touch the same block: they run on the original raw,
            # so compose: apply uitex edits first if this block is one of theirs
            import uitex
            if o in uitex.LZ3_BLOCKS + uitex.FRAME_BLOCKS: continue   # handled in uitex
            c = lz3.compress(new); cap = e - o
            assert len(c) <= cap, (hex(o), len(c), cap)
            img.write(img.pack_lba, o, c + bytes(cap - len(c))); n += 1
    return n

# ---- name-entry mode buttons (59x20 plates, glyph fill 7/8, light outline) ----
NE_BLOCK = 0x2fdbb8          # disc 1 CDPACK, LZ3
NE_FONT = __file__.rsplit('/', 1)[0] + '/font/koi7x14b.pil'
NE_BUTTONS = {(0, 0): 'АБВ', (64, 0): 'КАНДЗИ', (0, 24): 'абв', (64, 24): 'НАЗАД',
              (0, 48): 'ЗНАКИ', (64, 48): 'ГОТОВО'}
NE_BUTTONS = lang.tr(NE_BUTTONS)

def _text_mask(text, fontpath, bold=True):
    font = ImageFont.load(fontpath)
    t = text.encode('koi8-r').decode('latin-1')
    im = Image.new('1', (120, 16), 0); ImageDraw.Draw(im).text((0, 0), t, font=font, fill=1)
    m = np.array(im, dtype=bool)
    rows = np.nonzero(m.any(1))[0]; cols = np.nonzero(m.any(0))[0]
    m = m[rows.min():rows.max() + 1, :cols.max() + 1]
    if bold:
        h, w = m.shape; b = np.zeros((h, w + 1), dtype=bool); b[:, :w] |= m; b[:, 1:] |= m; m = b
    return m

def patch_ne(raw):
    px = to_px(raw)
    for (x, y), t in NE_BUTTONS.items():
        ix0, ix1, iy0, iy1 = x + 4, x + 54, y + 3, y + 17
        px[iy0:iy1, ix0:ix1] = 5
        m = _text_mask(t, NE_FONT, bold=False)
        h, w = m.shape
        ox = ix0 + ((ix1 - ix0) - w) // 2; oy = iy0 + ((iy1 - iy0) - h) // 2
        big = np.zeros(px.shape, dtype=bool); big[oy:oy + h, ox:ox + w] = m
        pad = np.pad(big, 1); near = np.zeros_like(big)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= pad[1 + dy:px.shape[0] + 1 + dy, 1 + dx:px.shape[1] + 1 + dx]
        px[near & ~big] = 12
        rows = np.arange(px.shape[0])[:, None]
        px[big & (rows < oy + h // 2)] = 8
        px[big & (rows >= oy + h // 2)] = 7
    return from_px(px)

def patch_ne_pack(img, p):
    if len(p) < NE_BLOCK + 4: return 0
    try: raw, e = lz3.decompress(p, NE_BLOCK)
    except Exception: return 0
    if len(raw) != 8192 or raw[7 * 64:7 * 64 + 8] != bytes.fromhex('326655558b777787'): return 0
    c = lz3.compress(patch_ne(raw)); cap = e - NE_BLOCK
    assert len(c) <= cap, (len(c), cap)
    img.write(img.pack_lba, NE_BLOCK, c + bytes(cap - len(c)))
    return 1

# ---- big 2-line button "セーブシステムヲ / ツクリナオス" (128x27) ----
BIG_REF = (0xd8988, 96)            # disc-3 block, top row
BIG_LINES = ('СОЗДАТЬ ЗАНОВО', 'СИСТЕМНЫЙ ФАЙЛ')
BIG_LINES = lang.tr(BIG_LINES)
BIG_H = 27

def big_ref_mask(pack3):
    raw, _ = lz3.decompress(pack3, BIG_REF[0])
    px = to_px(raw)
    return px[BIG_REF[1]:BIG_REF[1] + BIG_H, :] == 1

def draw_big(area):
    """area: 27x128 array view (modified in place)."""
    for r in range(2, BIG_H - 2):
        area[r, 3:125] = area[r, 124]
    for k, t in enumerate(BIG_LINES):
        m = render(t)
        h, w = m.shape
        ox = 3 + (122 - w) // 2; oy = 3 + k * 11 + (10 - h) // 2
        reg = area[oy:oy + h, ox:ox + w]; reg[m] = 1

def patch_big_blocks(blocks, refmask):
    """blocks: list of (offset, raw) in file order. Returns {offset: new_raw}."""
    pxs = [to_px(r) for _, r in blocks]; changed = set()
    for i, px in enumerate(pxs):
        for y in range(0, 128 - BIG_H + 1):
            if (px[y:y + BIG_H] == 1).shape == refmask.shape and ((px[y:y + BIG_H] == 1) == refmask).all():
                draw_big(px[y:y + BIG_H]); changed.add(i)
        if i + 1 < len(pxs):
            top = 128 - 16
            st = np.concatenate([px[top:], pxs[i + 1][top:top + BIG_H - 16]])
            if ((st == 1) == refmask).all():
                draw_big(st); px[top:] = st[:16]; pxs[i + 1][top:top + BIG_H - 16] = st[16:]
                changed.add(i); changed.add(i + 1)
    return {blocks[i][0]: from_px(pxs[i]) for i in changed}, pxs

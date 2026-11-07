"""Russian date in the top-left box: "1999年 5月24日(月)" -> "24.5.1999 (Пн)".

The box is a sprite 'animation' record set (12-byte records: x,y,u,v,w,h,tex,clut,..) that
holds the static glyphs 年 月 日 ( ) taken from the UI atlas; the digits and the weekday are
placed by code in the main overlay (constants patched here). 月/日 glyphs are also the
weekday cells, so the static records are repointed to a small dot sprite drawn in a free
corner of the atlas, and the weekday row of the atlas is redrawn in Russian (uitex.py)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import struct

OV = 0x800c0000
CODE = {            # overlay address: (old imm, new imm)   abs x = imm - slide
    0x800ea234: (-0xc2, -116),   # year, rightmost digit (then -12 per digit)
    0x800ea300: (-0xa4, -180),   # month tens
    0x800ea354: (-0x98, -168),   # month units
    0x800ea3f8: (-0x7c, -208),   # day tens
    0x800ea44c: (-0x70, -196),   # day units
    0x800ea0b8: (-0x4b, -94),    # weekday
    0x800e6ca8: (-0x4b, -94),    # weekday (init of the same sprite)
}
DOT_U, DOT_V, DOT_W = 48, 72, 5            # dot sprite in the atlas (free area)

def addiu_v0(imm): return 0x24020000 | (imm & 0xffff)

def _asm(src, addr):
    from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm('.set noreorder\n' + src, addr)[0])

# leading zeros: "5.5.1999" -> "05.05.1999"
ZERO = {   # addr: (old word, new asm)
    0x800ea2f0: (0x1440, 'sll $t5, $v0, 4'),          # was: bnez v0 (month < 10 -> skip tens)
    0x800ea2f4: (0x3c10, 'addiu $t6, $zero, 0x40'),   # was: lui s0,0x6666 (re-done at 0x800ea33c)
    0x800ea30c: (0x2402, 'subu $v0, $t6, $t5'),       # was: addiu v0,zero,0x40 ('1') -> '0' or '1'
    0x800ea3e8: (0x1440, 'nop'),                      # was: bnez v0 (day < 10 -> skip tens)
}

def overlay_patches(ov):
    out = []
    for a, (hi, src) in ZERO.items():
        o = a - OV
        assert struct.unpack_from('<I', ov, o)[0] >> 16 == hi, hex(a)
        out.append((o, _asm(src, a)))
    for a, (old, new) in CODE.items():
        o = a - OV
        assert struct.unpack_from('<I', ov, o)[0] == addiu_v0(old), hex(a)
        out.append((o, struct.pack('<I', addiu_v0(new))))
    return out

# record group: ')' '(' 日 月 年  (origin x = -256, y = -120)
def rec(x, y, u, v, w, h, tail=b'\0\0\0\0'):
    return struct.pack('<hhBBBB', x, y, u, v, w, h) + tail

def record_patches(p):
    """p: pack bytes. Returns list of (offset, bytes)."""
    out = []
    pat = rec(196, 22, 120, 0, 8, 16) + rec(173, 22, 112, 0, 8, 16) + rec(157, 22, 0, 0, 16, 16) \
        + rec(117, 22, 16, 0, 16, 16) + rec(78, 22, 32, 16, 16, 16, b'\0\0\x80\0')
    i = p.find(pat)
    while i >= 0:
        new = rec(178, 22, 120, 0, 8, 16) + rec(156, 22, 112, 0, 8, 16) + rec(157, 22, 0, 0, 0, 0) \
            + rec(74, 31, DOT_U, DOT_V, DOT_W, DOT_W) + rec(102, 31, DOT_U, DOT_V, DOT_W, DOT_W, b'\0\0\x80\0')
        out.append((i, new))
        i = p.find(pat, i + 1)
    return out

DOT = ['.111.',
       '18891',
       '189a1',
       '19aa1',
       '.111.']

WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
WEEKDAYS = lang.tr(WEEKDAYS)

def draw_atlas(px, font):
    """px: 128x128 numpy array of the atlas block (modified in place)."""
    import numpy as np
    from PIL import Image, ImageDraw
    # dot
    for y, row in enumerate(DOT):
        for x, c in enumerate(row):
            if c != '.': px[DOT_V + y, DOT_U + x] = int(c, 16)
    # weekdays: 16x16 cells at u = 16*i, v = 0; style of the original (outline 1, fill 8/9/a)
    for i, t in enumerate(WEEKDAYS):
        im = Image.new('1', (16, 16), 0); dr = ImageDraw.Draw(im)
        for k, ch in enumerate(t):
            dr.text((1 + k * 7, 1), ch.encode('koi8-r').decode('latin-1'), font=font, fill=1)
        m = np.array(im, dtype=bool)
        pad = np.pad(m, 1); near = np.zeros_like(m)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= pad[1 + dy:17 + dy, 1 + dx:17 + dx]
        cell = np.zeros((16, 16), dtype=px.dtype)
        cell[near] = 1
        rows = np.arange(16)[:, None].repeat(16, 1)
        fill = np.where(rows < 6, 8, np.where(rows < 10, 9, 10))
        cell[m] = fill[m]
        px[0:16, 16 * i:16 * i + 16] = cell

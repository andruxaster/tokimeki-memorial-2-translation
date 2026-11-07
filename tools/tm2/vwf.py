"""Narrow-font ("bigram cell") hack for Tokimeki Memorial 2.

Each 16px text cell shows TWO narrow (8px) glyphs. A cell is encoded as a
2-byte code: idx = a*N + b ; lead = 0xA0 + idx // 192 ; trail = 0x40 + idx % 192.
The exe glyph lookup 0x8001C5C0 (originally: 30 rare kanji + gaiji) is replaced:
  - bigram codes -> composed into a 30-byte Krom-format buffer
  - 0xF0xx gaiji -> original table (kept)
  - everything else -> 0 (BIOS font used, as before)
Font: symbols 0..63 at 0x80061874 (old rare-kanji table, 900 B),
      symbols 64..80 right after the new code.
Text renderers are patched to a 16px pitch (was 19px) so letters are evenly spaced.
"""
import sys, struct
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN
from font.mkfont import build as build_font, SYMBOLS, ROWS

N = len(SYMBOLS)
EXE_BASE = 0x80015000          # vaddr = EXE_BASE + file offset
FUNC = 0x8001C5C0
FUNC_END = 0x8001C874
F1 = 0x80061874                # 64 glyphs * 14 = 896 bytes (<= 900)
F1_COUNT = 64
SYMIDX = {c: i for i, c in enumerate(SYMBOLS)}

def hi(a): return ((a + 0x8000) >> 16) & 0xffff
def lo(a): return a & 0xffff if a & 0xffff < 0x8000 else (a & 0xffff) - 0x10000

def asm(F2, BUF):
    QL = int.from_bytes(cell_code(" ", "«"), "big"); QR = int.from_bytes(cell_code("»", " "), "big")
    src = f"""
.set noreorder
    andi  $t0, $a0, 0xffff
    ori   $t1, $zero, 0x8175
    bne   $t0, $t1, q1
    ori   $t1, $zero, 0x8176
    ori   $t0, $zero, {QL}
q1:
    bne   $t0, $t1, q2
    nop
    ori   $t0, $zero, {QR}
q2:
    srl   $t1, $t0, 8
    addiu $t1, $t1, -0xA0
    sltiu $t2, $t1, 35
    beqz  $t2, gaiji
    andi  $t3, $t0, 0xff
    addiu $t3, $t3, -0x40
    bltz  $t3, ret0
    sll   $t2, $t1, 6
    sll   $t4, $t1, 7
    addu  $t2, $t2, $t4
    addu  $t2, $t2, $t3
    sltiu $t4, $t2, {N*N}
    beqz  $t4, ret0
    addiu $t4, $zero, {N}
    divu  $zero, $t2, $t4
    mflo  $t5
    mfhi  $t6
    # glyph pointer A -> t8
    sltiu $t7, $t5, {F1_COUNT}
    bnez  $t7, a1f
    lui   $t8, {hi(F1)}
    addiu $t5, $t5, -{F1_COUNT}
    lui   $t8, {hi(F2)}
    b     a2f
    addiu $t8, $t8, {lo(F2)}
a1f:
    addiu $t8, $t8, {lo(F1)}
a2f:
    sll   $t7, $t5, 4
    sll   $t9, $t5, 1
    subu  $t7, $t7, $t9
    addu  $t8, $t8, $t7
    # glyph pointer B -> t9
    sltiu $t7, $t6, {F1_COUNT}
    bnez  $t7, b1f
    lui   $t9, {hi(F1)}
    addiu $t6, $t6, -{F1_COUNT}
    lui   $t9, {hi(F2)}
    b     b2f
    addiu $t9, $t9, {lo(F2)}
b1f:
    addiu $t9, $t9, {lo(F1)}
b2f:
    sll   $t7, $t6, 4
    sll   $v1, $t6, 1
    subu  $t7, $t7, $v1
    addu  $t9, $t9, $t7
    lui   $v0, {hi(BUF)}
    addiu $v0, $v0, {lo(BUF)}
    addiu $t0, $zero, {ROWS}
    move  $t1, $v0
loop:
    lbu   $t2, 0($t8)
    lbu   $t3, 0($t9)
    addiu $t8, $t8, 1
    addiu $t9, $t9, 1
    sb    $t2, 0($t1)
    sb    $t3, 1($t1)
    addiu $t0, $t0, -1
    bnez  $t0, loop
    addiu $t1, $t1, 2
    sh    $zero, 0($t1)
    jr    $ra
    nop
gaiji:
    andi  $t1, $t0, 0xf000
    ori   $t2, $zero, 0xf000
    bne   $t1, $t2, ret0
    andi  $t1, $t0, 0xf
    addiu $t1, $t1, 0x1e
    sll   $t2, $t1, 4
    subu  $t2, $t2, $t1
    sll   $t2, $t2, 1
    lui   $v0, {hi(F1)}
    addiu $v0, $v0, {lo(F1)}
    jr    $ra
    addu  $v0, $v0, $t2
ret0:
    jr    $ra
    move  $v0, $zero
"""
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    enc, _ = ks.asm(src, FUNC)
    return bytes(enc)

def exe_patches():
    """Returns list of (vaddr, bytes) for the executable."""
    glyphs = build_font()
    code = asm(0, 0)                      # size probe
    BUF = (FUNC + len(code) + 3) & ~3
    F2 = BUF + 32
    code = asm(F2, BUF)
    assert BUF >= FUNC + len(code)
    f2 = b''.join(glyphs[F1_COUNT:])
    assert F2 + len(f2) <= 0x8001c7d4, hex(F2 + len(f2))
    f1 = b''.join(glyphs[:F1_COUNT])
    assert len(f1) <= 900
    return [(FUNC, code), (BUF, bytes(32)), (F2, f2), (F1, f1)]

# ---------- text encoding ----------
def cell_code(a, b):
    idx = SYMIDX[a] * N + SYMIDX[b]
    return bytes([0xA0 + idx // 192, 0x40 + idx % 192])

import os as _o, re as _re
_EN = _o.environ.get('TM2_LANG') == 'en'; _CYR = _re.compile('[А-Яа-яЁё]')

def encode(text):
    """Unicode text -> plain (unswapped) game bytes. Narrow symbols are paired
    into cells; anything else is emitted as a normal full-width SJIS char."""
    if _EN and _CYR.search(text): raise ValueError('Cyrillic in English build: %r' % text)
    out = bytearray(); pend = None
    for ch in text:
        if ch == 'ё' and 'ё' not in SYMIDX: ch = 'е'
        if ch == 'Ё': ch = 'Е'
        if ch == 'Ъ': ch = 'ъ'
        if ch == ';': ch = ','
        if ch in '’‘': ch = "'"
        if ch in '“”': ch = '"'
        if ch == "'" and ch not in SYMIDX: ch = '"'
        if ch not in SYMIDX and '!' <= ch <= '~': ch = chr(ord(ch) + 0xFEE0)   # ASCII -> full-width
        if ch == '—' or ch == '–': ch = '-'
        if ch in SYMIDX:
            if pend is None: pend = ch
            else: out += cell_code(pend, ch); pend = None
        else:
            if pend is not None: out += cell_code(pend, ' '); pend = None
            out += ch.encode('cp932')
    if pend is not None:
        out += cell_code(pend, ' ')
    return bytes(out)

def cells(text):
    return len(encode(text)) // 2

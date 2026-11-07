"""Russian name entry (overlay loaded at 0x800c0000; disc 1).

* The kana grid tables are replaced by Cyrillic letters (each grid item is a narrow-font
  cell 'letter + space').
* The 'append character' code is redirected to a small hook that packs two letters into
  one cell: when the new item is a single-letter cell and the last stored cell also holds
  one letter, they are merged.  So the 3-cell name fields hold up to 6 letters.
  The hook lives in the kanji table of the 'し' reading (that kanji list becomes garbage).
* Prompts and labels are translated in place (fixed-width fields padded with blank cells).
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, struct
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN

OVB = 0x800c0000
TABLE0 = 0x360            # overlay offset of 'ー～' (first of the kana tables)
APPEND = 0x8804           # overlay offset: lh v1,0x1fc(s0) ; lh v0,0x10(a2)
HOOK = 0x14a0             # overlay offset of the 'し' kanji list (794 bytes)
RET_DONE = 0x800c896c
RET_ORIG = 0x800c880c

# kana tables (overlay offset -> 5-char row). Rows in screen order: group 1 (あかさたな),
# group 2 (はまやらわ), group 3 (がざだばぱ), group 4 (ぁ っ ー～)
ROWS = [0x428, 0x41c, 0x410, 0x404, 0x3f8,
        0x3ec, 0x3e0, 0x3d4, 0x3c8, 0x3bc,
        0x3b0, 0x3a4, 0x398, 0x38c, 0x380,
        0x374, 0x368]
KATA = 0x434 - 0x368      # katakana rows are the same layout, shifted
UPPER = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ'
LOWER = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
if lang.EN:
    UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'; LOWER = 'abcdefghijklmnopqrstuvwxyz'
LETTERS = list(UPPER + LOWER + '-.')
if lang.EN:     # 5x5 groups: A-Y | a-y | Z z - . '
    LETTERS = list('ABCDEFGHIJKLMNOPQRSTUVWXY' + 'abcdefghijklmnopqrstuvwxy' + "Zz-.'")

def grid_rows():
    out = []; k = 0
    for i, off in enumerate(ROWS):
        row = b''
        for j in range(5):
            if k < len(LETTERS): row += vwf.cell_code(LETTERS[k], ' '); k += 1
            else: row += '　'.encode('cp932')
        out.append((off, row))
    assert k >= len(LETTERS), k
    return out

def hook_code():
    N = vwf.N
    src = f'''
.set noreorder
    lh    $v0, 0x10($a2)
    lw    $a0, 4($a2)
    sll   $v0, $v0, 1
    addu  $v0, $v0, $a0
    lbu   $t1, 0($v0)
    lbu   $t2, 1($v0)
    addiu $t3, $t1, -0xA0
    sltiu $t4, $t3, 35
    beqz  $t4, orig
    nop
    sll   $t4, $t3, 7
    sll   $t3, $t3, 6
    addu  $t3, $t3, $t4
    addiu $t2, $t2, -0x40
    addu  $t3, $t3, $t2
    addiu $t4, $zero, {N}
    divu  $zero, $t3, $t4
    mfhi  $t5
    mflo  $t6
    bnez  $t5, orig
    nop
    lh    $t0, 0x1fc($s0)
    nop
    sll   $t7, $t0, 1
    addu  $t7, $t7, $a1
    lbu   $t8, 0($t7)
    nop
    bnez  $t8, haveq
    nop
    beqz  $t0, orig
    addiu $t7, $t7, -2
haveq:
    lbu   $t8, 0($t7)
    lbu   $t9, 1($t7)
    addiu $t8, $t8, -0xA0
    sltiu $v1, $t8, 35
    beqz  $v1, orig
    sll   $v1, $t8, 7
    sll   $t8, $t8, 6
    addu  $t8, $t8, $v1
    addiu $t9, $t9, -0x40
    addu  $t8, $t8, $t9
    divu  $zero, $t8, $t4
    mfhi  $v1
    nop
    bnez  $v1, orig
    nop
    addu  $t8, $t8, $t6
    addiu $v1, $zero, 192
    divu  $zero, $t8, $v1
    mflo  $v0
    mfhi  $v1
    addiu $v0, $v0, 0xA0
    addiu $v1, $v1, 0x40
    sb    $v0, 0($t7)
    j     {RET_DONE}
    sb    $v1, 1($t7)
orig:
    lh    $v1, 0x1fc($s0)
    j     {RET_ORIG}
    lh    $v0, 0x10($a2)
'''
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm(src, OVB + HOOK)[0])

def jump_code():
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm(f'.set noreorder\n j {OVB + HOOK}\n nop', OVB + APPEND)[0])

FIXED = {   # overlay offset: (jp, ru)   exact length, blank-cell padding
    0x188: ('これでいい？', 'Всё верно?'),
    0x198: ('誕生日と血液型も教えてくれる？', 'День рождения и группа крови?'),
    0x1b8: ('読みかたを入力しますか（仮）？', 'Ввести чтение имени?'),
    0x1d8: ('名前は？', 'Имя?'),
    0x1e4: ('君の苗字を教えて？', 'Твоя фамилия?'),
    0x1fc: ('誕生日：　　月　　日', 'Д.р.м.д:　　. 　　  '),
    0x214: ('血液型：　　型', 'Группа:　　　'),
    0x224: ('はい　', 'Да'),
    0x22c: ('いいえ', 'Нет'),
    0x234: ('名　前：', 'Имя:'),
    0x240: ('名前：', 'Имя:'),
}
FIXED = lang.tr(FIXED)

def patches(ov):
    """ov: overlay bytes (from its base). Returns [(offset, bytes)]."""
    out = []
    assert ov[TABLE0:TABLE0 + 4] == 'ー～'.encode('cp932')
    assert struct.unpack_from('<I', ov, APPEND)[0] == 0x860301fc, hex(struct.unpack_from('<I', ov, APPEND)[0])
    assert struct.unpack_from('<I', ov, APPEND + 4)[0] == 0x84c20010
    assert ov[HOOK:HOOK + 4] == '仕仔'.encode('cp932')
    for off, row in grid_rows():
        assert len(row) == 10
        out.append((off, row))
        out.append((off + KATA, row))
    out.append((HOOK, hook_code()))
    out.append((APPEND, jump_code()))
    blank = vwf.cell_code(' ', ' ')
    for off, (jp, ru) in FIXED.items():
        jb = jp.encode('cp932'); assert ov[off:off + len(jb)] == jb, (hex(off), jp)
        rb = vwf.encode(ru); assert len(rb) <= len(jb), (jp, ru)
        out.append((off, rb + blank * ((len(jb) - len(rb)) // 2)))
    return out

def patch_pack(img, p):
    n = 0
    key = 'ー～'.encode('cp932') + b'\0\0\0\0' + 'っゃゅょゎ'.encode('cp932')
    i = p.find(key)
    while i >= 0:
        base = i - TABLE0
        ov = p[base:base + 0x10000]
        try:
            ps = patches(ov)
        except AssertionError:
            i = p.find(key, i + 1); continue
        for off, b in ps: img.write(img.pack_lba, base + off, b)
        n += 1
        i = p.find(key, i + 1)
    return n

if __name__ == '__main__':
    p = open(sys.argv[1], 'rb').read()
    key = 'ー～'.encode('cp932') + b'\0\0\0\0' + 'っゃゅょゎ'.encode('cp932')
    i = p.find(key)
    while i >= 0:
        try: print(hex(i - TABLE0), len(patches(p[i - TABLE0:i - TABLE0 + 0x10000])), 'patches')
        except AssertionError as e: print(hex(i - TABLE0), 'skip', e)
        i = p.find(key, i + 1)
    print(len(hook_code()), 'hook bytes')

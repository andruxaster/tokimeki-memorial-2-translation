"""Russian names for inline text tokens ({1x}/{2x}) of the main overlay.

Name slots in the overlay (0x800c132c..0x800c1490) are copied by inlined fixed-length
copies, so each slot gets a 3-byte macro [0xD0|hi, lo, 0] pointing to the real Russian
string (offset from 0x800c1000), which is stored in free tails of the slots.
The builder's three strcpy() calls are redirected to a tiny exe hook that expands macros.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, re, struct
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN

OV_BASE = 0x800c0000
REGION = (0x132c, 0x1490)
MACRO_BASE = 0x80061bf8   # old gaiji table in the exe (unused by text), 480 bytes
NAMES_MAX = 270          # gaiji glyphs end at 0x80061d06 (data follows!)
STRCPY = 0x8005a074
CALLS = (0x23a94, 0x23b24, 0x23c14)     # overlay offsets of jal strcpy in the builder
HOOK = 0x8001c7d4                       # in the exe, after the font (free up to 0x8001c874)
CHARHOOK = 0x8001c808

RU = {
    'メイ様': 'госпожа Мэй', 'メイ': 'Мэй', '伊集院': 'Идзюин', 'マネージャー': 'менеджер',
    '楓子': 'Каэдэко', '佐倉': 'Сакура', '花桜梨': 'Каори', '八重': 'Яэ', '会長': 'президент',
    'ほむら': 'Хомура', '赤井': 'Акаи', 'みほぴょん': 'Михопон', '美帆': 'Михо', '白雪': 'Сираюки',
    '茜ちん': 'Аканэчка', '茜': 'Аканэ', '一文字': 'Итимондзи', 'ゆっきー': 'Юкки', '美幸': 'Миюки',
    '寿': 'Котобуки', '琴子': 'Котоко', '水無月': 'Минадзуки', '光': 'Хикари', '陽ノ下': 'Хиномото',
    '華澄': 'Касуми', '麻生': 'Асо', '匠': 'Такуми', '純': 'Дзюн',
    '麻生先生': 'учитель Асо', '華澄先生': 'Касуми',
    'さん': '', 'ちゃん': '', '君': '', 'くん': '',
    'あなた': 'ты', 'キミ': 'ты', 'お前': 'ты', '貴様': 'ты', '……': '…',
}
RU = lang.tr(RU)

def hook_code():
    src = f"""
.set noreorder
    lbu   $t0, 0($a1)
    nop                       # load delay slot
    addiu $t1, $t0, -0xD0
    sltiu $t2, $t1, 16
    beqz  $t2, go
    lbu   $t3, 1($a1)
    sll   $t1, $t1, 8
    or    $t1, $t1, $t3
    lui   $a1, 0x8006
    addiu $a1, $a1, 0x1bf8
    addu  $a1, $a1, $t1
go:
    j     {STRCPY}
    nop
"""
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm(src, HOOK)[0])

def slots(ov):
    seg = ov[REGION[0]:REGION[1]]
    starts = []
    for m in re.finditer(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\xfc])+\x00', seg):
        if (REGION[0] + m.start()) % 4 == 0:
            starts.append((REGION[0] + m.start(), m.group()[:-1].decode('cp932')))
    out = []
    for i, (s, t) in enumerate(starts):
        e = starts[i + 1][0] if i + 1 < len(starts) else REGION[1]
        out.append((s, e, t))
    return out

CHARJ = 0x23a1c          # overlay offset of 'j 0x800e4024' after a 2-byte char in the builder
LOOPTAIL = 0x800e4024


def charhook_code(addr):
    src = f'''
.set noreorder
    lbu   $t0, -1($s0)
    nop
    addiu $t1, $t0, -0xD0
    sltiu $t2, $t1, 16
    beqz  $t2, back
    lbu   $t3, 0($s0)
    sll   $t1, $t1, 8
    or    $t1, $t1, $t3
    lui   $t4, 0x8006
    addiu $t4, $t4, 0x1bf8
    addu  $t4, $t4, $t1
    addiu $s0, $s0, -1
    addiu $s1, $s1, -2
cp:
    lbu   $t5, 0($t4)
    nop
    beqz  $t5, done
    nop
    sb    $t5, 0($s0)
    addiu $t4, $t4, 1
    addiu $s0, $s0, 1
    b     cp
    addiu $s1, $s1, 1
done:
    addiu $s0, $s0, -1
back:
    j     {LOOPTAIL}
    nop
'''
    ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm(src, addr)[0])

class Blob:
    def __init__(self): self.b = bytearray(); self.where = {}
    def add(self, ru):
        if ru not in self.where:
            e = vwf.encode(ru) + b'\0'
            if lang.EN:     # English: reuse the tail of an existing string (cell aligned)
                for k, o in list(self.where.items()):
                    ke = vwf.encode(k) + b'\0'; d = len(ke) - len(e)
                    if d > 0 and d % 2 == 0 and ke.endswith(e) and (o + d) & 0xff:
                        self.where[ru] = o + d; break
            if ru not in self.where:
                if len(self.b) & 0xff == 0: self.b += b'\0'
                self.where[ru] = len(self.b); self.b += e
        off = self.where[ru]
        return bytes([0xD0 | (off >> 8), off & 0xff])

SPEAKER_TSV = __file__.rsplit('/', 1)[0] + ('/lang/en_speakers.tsv' if lang.EN else '/speaker_labels.tsv')

def load_speakers():
    d = {}
    for ln in open(SPEAKER_TSV, encoding='utf-8'):
        if '\t' in ln and not ln.startswith('#'):
            jp, ru = ln.rstrip('\n').split('\t')[:2]
            d[jp] = ru
    return d

# deterministic blob: identical on every disc (disc 1's exe serves all discs)
BLOB = Blob()
for _ru in RU.values():
    if _ru: BLOB.add(_ru)
SPEAKERS = load_speakers()
for _jp in sorted(SPEAKERS):
    if len(vwf.encode(SPEAKERS[_jp])) > len(_jp.encode('cp932')):   # only labels that do not fit in place
        BLOB.add(SPEAKERS[_jp])

def macro(ru):
    assert ru in BLOB.where, ru
    return BLOB.add(ru)

def build_tables(ov):
    """Returns (overlay_patches, names_blob). names_blob goes to MACRO_BASE in the exe."""
    sl = slots(ov)
    patches = []
    for s, e, t in sl:
        if t not in RU: continue
        ru = RU[t]
        if ru == '':
            patches.append((s, b'\0')); continue
        assert e - s >= 3
        patches.append((s, BLOB.add(ru) + b'\0'))
    return patches, None

def blob_with_code():
    """Final exe data for MACRO_BASE: strings + char hook at the end. Returns (bytes, hook_addr)."""
    assert len(BLOB.b) <= NAMES_MAX, len(BLOB.b)
    assert HOOK + len(hook_code()) <= CHARHOOK
    code = charhook_code(CHARHOOK)
    assert CHARHOOK + len(code) <= 0x8001c874, hex(CHARHOOK + len(code))
    return bytes(BLOB.b), code

def overlay_patches(ov):
    patches, blob = build_tables(ov)
    jal = 0x0c000000 | ((HOOK >> 2) & 0x3ffffff)
    for c in CALLS:
        assert struct.unpack_from('<I', ov, c)[0] == 0x0c000000 | ((STRCPY >> 2) & 0x3ffffff)
        patches.append((c, struct.pack('<I', jal)))
    assert struct.unpack_from('<I', ov, CHARJ)[0] == 0x08000000 | ((LOOPTAIL >> 2) & 0x3ffffff)
    return patches

def charj_patch(hook_addr):
    return (CHARJ, struct.pack('<I', 0x08000000 | ((hook_addr >> 2) & 0x3ffffff)))

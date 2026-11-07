"""Patch bytes inside CDPACK00.BIN of the raw BIN image, fixing EDC/ECC."""
import sys, shutil
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from cdsector import build_mode2_form1
PACK_LBA = 536

def patch(bin_path, patches, pack_lba=PACK_LBA):
    """patches: list of (pack_offset, bytes) in ORIGINAL (on-disc) encoding."""
    bysec = {}
    for off, data in patches:
        for i, b in enumerate(data):
            o = off + i
            bysec.setdefault(o // 2048, {})[o % 2048] = b
    with open(bin_path, 'r+b') as f:
        for sec, mods in bysec.items():
            lba = pack_lba + sec
            f.seek(lba * 2352)
            s = bytearray(f.read(2352))
            for k, v in mods.items():
                s[24 + k] = v
            build_mode2_form1(s)
            f.seek(lba * 2352)
            f.write(s)
    return len(bysec)

SWAP = bytes(((i & 15) << 4) | (i >> 4) for i in range(256))
def enc_text(s):
    """Unicode -> on-disc nibble-swapped Shift-JIS."""
    return s.encode('cp932').translate(SWAP)

"""CD-ROM Mode 2 Form 1 sector EDC/ECC generation (ECMA-130)."""
_edc = []
for i in range(256):
    e = i
    for _ in range(8):
        e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    _edc.append(e)
_ecc_f = [0] * 256
_ecc_b = [0] * 256
for i in range(256):
    j = (i << 1) ^ (0x11D if i & 0x80 else 0)
    _ecc_f[i] = j & 0xFF
    _ecc_b[i ^ j & 0xFF] = i


def edc(data):
    e = 0
    for b in data:
        e = (e >> 8) ^ _edc[(e ^ b) & 0xFF]
    return e


def _ecc_pq(sector, major_count, minor_count, major_mult, minor_inc, out_off):
    # operates on sector[12:] (address+data), as in standard implementation
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = 0
        ecc_b = 0
        for minor in range(minor_count):
            temp = sector[12 + index]
            index += minor_inc
            if index >= size:
                index -= size
            ecc_a ^= temp
            ecc_b ^= temp
            ecc_a = _ecc_f[ecc_a]
        ecc_a = _ecc_b[_ecc_f[ecc_a] ^ ecc_b]
        sector[out_off + major] = ecc_a
        sector[out_off + major + major_count] = ecc_a ^ ecc_b


def build_mode2_form1(sector):
    """sector: bytearray(2352) with sync/header/subheader and user data set.
    Recomputes EDC (0x818) and ECC P/Q (0x81C..0x92F)."""
    e = edc(sector[16:16 + 8 + 2048])
    sector[0x818:0x81C] = e.to_bytes(4, 'little')
    saved = bytes(sector[12:16])
    sector[12:16] = b'\0\0\0\0'  # header zeroed for ECC in mode 2
    _ecc_pq(sector, 86, 24, 2, 86, 0x81C)
    _ecc_pq(sector, 52, 43, 86, 88, 0x8C8)
    sector[12:16] = saved
    return sector

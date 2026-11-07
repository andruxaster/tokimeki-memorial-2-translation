"""Find script strings in nibble-swapped view. Returns (offset, kind, text, capacity_bytes)."""
import re
SJ = rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc])+'
PAT = re.compile(rb'([\x01\x81])(' + SJ + rb')\x00')
def find(y, start, end):
    out = []
    for m in PAT.finditer(y, start, end):
        b = m.group(2)
        if m.group(1) == b'\x81':
            # speaker: the 0x81 is opcode; name bytes follow
            pass
        try: s = b.decode('cp932')
        except UnicodeDecodeError: continue
        out.append((m.start(2), 'name' if m.group(1) == b'\x81' else 'text', s, len(b)))
    return out

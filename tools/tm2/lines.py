"""Script line parser for the nibble-swapped TM2 message format.

A text line starts with 0x01 or 0x11 and ends with 0x00. Inside: SJIS pairs (text)
and control bytes:
  0x10-0x2d  : 1-byte inline code (0x1d/0x1e = player name, 0x2x = variables)
  0x2e, 0x2f : code + 1 arg byte
  0x30-0x3f  : code + 1 arg byte
Templates use {xx} / {xx:yy} tokens for controls.
"""
import re

LEAD = set(range(0x81, 0x85)) | set(range(0x88, 0xa0)) | set(range(0xe0, 0xeb))

def parse_line(y, p):
    """p points to first byte after the 0x01/0x11 start code. Returns (template, end) or None."""
    out = []; i = p; text = 0
    while i < len(y):
        b = y[i]
        if b == 0:
            return ''.join(out), i, text
        if b in LEAD:
            if i + 1 >= len(y): return None
            t = y[i + 1]
            if not (0x40 <= t <= 0xfc) or t == 0x7f: return None
            try: ch = bytes(y[i:i + 2]).decode('cp932')
            except UnicodeDecodeError: return None
            if ch in '{}': return None
            out.append(ch); i += 2; text += 1
        elif 0x10 <= b <= 0x2d:
            out.append('{%02x}' % b); i += 1
        elif b == 0x0c and i + 1 < len(y) and y[i + 1] == 0:     # 'continue on the same line'
            out.append('{0c}'); i += 1
        elif b in (0x2e, 0x2f) or 0x30 <= b <= 0x3f:
            if i + 1 >= len(y): return None
            out.append('{%02x:%02x}' % (b, y[i + 1])); i += 2
        else:
            return None
        if i - p > 200: return None
    return None

TOK = re.compile(r'\{([0-9a-f]{2})(?::([0-9a-f]{2}))?\}')

def template_bytes(tpl, encode_text):
    """Encode a (translated) template back to plain game bytes."""
    out = bytearray(); pos = 0
    for m in TOK.finditer(tpl):
        if m.start() > pos: out += encode_text(tpl[pos:m.start()])
        out.append(int(m.group(1), 16))
        if m.group(2): out.append(int(m.group(2), 16))
        pos = m.end()
    if pos < len(tpl): out += encode_text(tpl[pos:])
    return bytes(out)

def tokens(tpl):
    return TOK.findall(tpl)

def scan(y):
    """Yield (offset_of_content, start_code, template, length_bytes, n_text_chars)."""
    i = 0; n = len(y)
    for m in re.finditer(rb'[\x01\x11](?=[\x81-\x84\x88-\x9f\xe0-\xea\x10-\x3f])', y):
        p = m.start() + 1
        r = parse_line(y, p)
        if not r: continue
        tpl, end, text = r
        if text == 0: continue
        yield p, y[m.start()], tpl, end - p, text

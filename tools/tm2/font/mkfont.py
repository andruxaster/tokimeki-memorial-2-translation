"""Build the 8x14 narrow font (koi7x14 based) for the bigram glyph hook."""
from PIL import ImageFont, Image, ImageDraw
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lang
if lang.EN:      # « » are drawn as curly quotes in the English font
    SYMBOLS = (' ' + 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789' +
               '.,!?-:…"()«»' + "'/")
else:
    SYMBOLS = (' ' + 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' +
               'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ' + '.,!?-:…"()«»')
assert len(SYMBOLS) == 77, len(SYMBOLS)
ROWS = 14
def build(pil=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'koi7x14.pil')):
    f = ImageFont.load(pil)
    glyphs = []
    for ch in SYMBOLS:
        img = Image.new('1', (8, ROWS), 0)
        d = ImageDraw.Draw(img)
        if ch == '…':
            for x in (0, 3, 6): img.putpixel((x, 11), 1)   # baseline dots
        elif ch in '«»' and lang.EN:            # curly double quotes
            img = Image.new('1', (8, ROWS), 0)
            pts = [(1, 2), (1, 3), (2, 1), (2, 4)] if ch == '«' else [(1, 1), (1, 4), (2, 2), (2, 3)]
            for dx in (0, 3):
                for x, y in pts: img.putpixel((x + dx, y + 1), 1)
        elif ch in '«»':
            d.text((0, 0), ('<<' if ch == '«' else '>>').encode('latin-1').decode('latin-1')[:1], font=f, fill=1)
            # simple custom guillemets
            img = Image.new('1', (8, ROWS), 0)
            pts = [(2,0),(1,1),(0,2),(1,3),(2,4)]
            for dx in (0, 3):
                for x, y in pts:
                    xx = (x if ch == '«' else 2 - x) + dx
                    img.putpixel((xx, y + 6), 1)
        else:
            d.text((0, 0), ch.encode('koi8-r').decode('latin-1'), font=f, fill=1)
        rows = []
        for y in range(ROWS):
            v = 0
            for x in range(8):
                if img.getpixel((x, y)): v |= 0x80 >> x
            rows.append(v)
        glyphs.append(bytes(rows))
    return glyphs
if __name__ == '__main__':
    g = build()
    big = Image.new('L', (81 * 9, ROWS), 40)
    for i, rows in enumerate(g):
        for y, v in enumerate(rows):
            for x in range(8):
                if v & (0x80 >> x): big.putpixel((i * 9 + x, y), 255)
    big.resize((big.width * 3, big.height * 3), Image.NEAREST).save('font_sheet.png')

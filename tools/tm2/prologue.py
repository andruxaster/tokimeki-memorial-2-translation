"""Childhood (disc 1 prologue) UI strings: location names of the map screen.

* Prologue overlay location table: 20-byte records = 18 bytes SJIS padded with '　' + 2 zeros.
  Russian text is narrow-encoded and padded with blank cells to the same 18 bytes.
* Map-file location records (amusement park etc.): 4-byte header + zero-padded SJIS, 32 bytes;
  Russian text is written zero-padded (max 26 bytes, like the main-game location records)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf

LOC = {
    'ひびきの高校前': 'У школы Хибикино',
    '華澄宅前': 'У дома Касуми',
    '光宅前': 'У дома Хикари',
    'ひびきの小学校': 'Начальная школа',
    '伊集院邸前大橋': 'Мост Идзюин',
    '大通り': 'Проспект',
    'ひびきの駅前': 'У станции',
    '踏切': 'Переезд',
    '河川敷き公園': 'Парк у реки',
    '河川敷き': 'Берег реки',
    '自宅前': 'У дома',
    '駄菓子屋前': 'У лавки сладостей',
    'ひびきの神社': 'Храм Хибикино',
    '小さな公園': 'Маленький парк',
    '図書館公園': 'Парк у библиотеки',
    'ひびきの商店街': 'Торговая улица',
    '山道': 'Горная тропа',
    '教室': 'Класс',
    '道路': 'Дорога',
    '小さな公園前': 'У маленького парка',
    '小さな公園・桜祭り': 'Праздник сакуры',
    '児童図書館': 'Детская библиотека',
    '遊園地入口': 'Вход в луна-парк',
    '遊園地': 'Луна-парк',
}
LOC = lang.tr(LOC)

SP = '　'.encode('cp932')
BLANK = vwf.cell_code(' ', ' ')

def table_patches(p):
    """20-byte record table (prologue overlay)."""
    out = []
    first = ('ひびきの高校前　　'.encode('cp932') + b'\0\0' + '華澄宅前'.encode('cp932'))
    i = p.find(first)
    while i >= 0:
        o = i
        while True:
            rec = p[o:o + 20]
            if len(rec) < 20 or rec[18:20] != b'\0\0': break
            try: s = rec[:18].decode('cp932')
            except UnicodeDecodeError: break
            jp = s.rstrip('　')
            if jp:
                if jp not in LOC: break
                rb = vwf.encode(LOC[jp]); assert len(rb) <= 18, jp
                out.append((o, rb + BLANK * ((18 - len(rb)) // 2)))
            o += 20
        i = p.find(first, i + 1)
    return out

def record_patches(p):
    """32-byte map records: <2B id><2B ?><SJIS ...zeros> (string field 28 bytes)."""
    import re
    out = []
    for jp in ('自宅前', '遊園地入口', '遊園地'):     # amusement-park day map records (disc 1)
        ru = LOC[jp]; jb = jp.encode('cp932')
        for m in re.finditer(re.escape(jb) + b'\0', p):
            o = m.start()
            field = p[o:o + 28]
            if field[len(jb):] != bytes(28 - len(jb)): continue
            # header: small id, then a coordinate-like word; previous record ends with zeros or 0xffff
            hdr = p[o - 4:o]
            if hdr[1] != 0: continue
            rb = vwf.encode(ru); assert len(rb) <= 26, ru
            out.append((o, rb + bytes(28 - len(rb))))
    return out

# plain SJIS strings of the prologue overlays (hero's monologues on the map, the "7 years
# later" transition).  Lines are separated by "\n " as in the original.
PLAIN = {
    'おっきな川…\n お魚がたくさんいるのかな？\n 深いのかな？': 'Большая река…\n Интересно, тут много рыбы?\n А глубоко тут?',
    'おっきな川…\n 落ちないように気をつけなきゃ。': 'Большая река…\n Главное - не свалиться.',
    '超戦士ドラゴンチョコたべたいな…）': 'Хочу шоколадку «Супервоин-Дракон»…)',
    '超戦士ドラゴンチョコたべようかな…）': 'Может, съесть «Супервоина-Дракона»…)',
    'おみくじ、ひこーかな…）': 'Может, вытянуть предсказание…)',
    'おみくじ、ひこーっと。': 'Вытяну-ка предсказание!',
    'いつみても、ちっちゃい図書館…）': 'Какая всё-таки маленькая библиотека…)',
    '今日は本でもよもーかな。': 'Может, почитать сегодня книжку?',
    'あれから７年': 'Прошло 7 лет',
    '帰ってきたんだなぁ。': 'Вот я и вернулся.',
    'あっ、ひびきの高校だ。': 'О, школа Хибикино!',
}
PLAIN = lang.tr(PLAIN)
PLAIN_SHORT = {'か…': 'И…', '……': '…'}     # only right after 'あれから７年'
PLAIN_SHORT = lang.tr(PLAIN_SHORT)

def enc_lines(ru):
    return b'\n '.join(vwf.encode(x) for x in ru.split('\n '))

def plain_patches(p):
    import re
    out = []
    for jp, ru in PLAIN.items():
        jb = jp.encode('cp932')
        for m in re.finditer(re.escape(jb) + b'\0', p):
            o = m.start()
            if p[o - 1] not in (0, 1, 2): continue
            e = o + len(jb)
            while e < len(p) and p[e] == 0 and e - o < 0x84: e += 1
            cap = e - o - 1
            rb = enc_lines(ru)
            assert len(rb) <= cap, (jp, len(rb), cap)
            out.append((o, rb + bytes(e - o - len(rb))))
            if jp == 'あれから７年':
                q = (e + 3) & ~3
                for sj, sr in PLAIN_SHORT.items():
                    sb = sj.encode('cp932')
                    k = p.find(sb + b'\0', e, e + 0x20)
                    if k >= 0:
                        rb = vwf.encode(sr); out.append((k, rb + bytes(len(sb) - len(rb))))
    return out

def patch_pack(img, p):
    ps = table_patches(p)
    if not ps: return 0              # not disc 1
    ps += record_patches(p) + plain_patches(p)
    for o, b in ps: img.write(img.pack_lba, o, b)
    import prodate
    return len(ps) + prodate.patch_pack(img, p)

if __name__ == '__main__':
    p = open(sys.argv[1], 'rb').read()
    for o, b in table_patches(p) + record_patches(p): print(hex(o), len(b))

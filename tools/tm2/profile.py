"""Takumi's notebook (friend's info on the girls) - overlay data tables.

The page draws every field with a fixed number of characters, so Russian text is padded
with blank cells to the original field length (zero bytes would be drawn as junk).
Fields: full names (12 bytes), the "ask about" surname list (variable), birthday (18),
zodiac + blood type (18), height (16).  Memo lines and clubs come from the plain-string
table (plainapply pads them the same way)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf

BLANK = vwf.cell_code(' ', ' ')
ANCHOR = '穂刈　純一郎'.encode('cp932')

NAMES = {'穂刈　純一郎': 'Дзюн', '坂城　　　匠': 'Такуми', '麻生　　華澄': 'Касуми', '伊集院　メイ': 'Мэй',
         '佐倉　　楓子': 'Каэдэко', '八重　花桜梨': 'Каори', '赤井　ほむら': 'Хомура', '白雪　　美帆': 'Михо',
         '一文字　　茜': 'Аканэ', '寿　　　美幸': 'Миюки', '水無月　琴子': 'Котоко', '陽ノ下　　光': 'Хикари'}
NAMES = lang.tr(NAMES)
SURN = {'陽ノ下': 'Хикари', '水無月': 'Котоко', '一文字': 'Аканэ', '白雪': 'Михо', '赤井': 'Хомура',
        '八重': 'Каори', '佐倉': 'Каэдэ', '伊集院': 'Мэй', '麻生': 'Касуми', '坂城': 'Такуми', '穂刈': 'Дзюн'}
SURN = lang.tr(SURN)
ZOD = {'乙女座': 'Дева', '天秤座': 'Весы', '蠍座': 'Скорпион', '牡牛座': 'Телец', '蟹座': 'Рак',
       '魚座': 'Рыбы', '山羊座': 'Козерог', '射手座': 'Стрелец'}
ZOD = lang.tr(ZOD)
FW = str.maketrans('０１２３４５６７８９', '0123456789')

def ru_for(jp):
    if jp in NAMES: return NAMES[jp], True
    if jp in SURN: return SURN[jp], False
    # digits: full-width in the Russian build (no narrow digits), narrow in the English one
    dig = (lambda t: t) if lang.EN else (lambda t: t.translate(str.maketrans('0123456789', '０１２３４５６７８９')))
    m = re.fullmatch(r'　?([０-９]+)月　?([０-９]+)日生まれ', jp)
    if m:
        mo, d = int(m.group(1).translate(FW)), int(m.group(2).translate(FW))
        if lang.EN: return lang.t('Род. %s.%s') % (dig(str(mo).zfill(2)), dig(str(d).zfill(2))), True
        return 'Род. %s.%s' % (dig(str(d).zfill(2)), dig(str(mo).zfill(2))), True
    m = re.fullmatch(r'　?(\S+座)　+(Ａ|Ｂ|Ｏ|ＡＢ)型', jp)
    if m:
        bt = m.group(2).translate(str.maketrans('ＡＢＯ', 'ABO')) if lang.EN else m.group(2)
        return lang.t('%s, кр.%s') % (ZOD[m.group(1)], bt), True
    m = re.fullmatch(r'身長／([０-９]+)ｃｍ', jp)
    if m: return lang.t('Рост: %s см') % (m.group(1).translate(FW) if lang.EN else m.group(1)), True
    return None, False

def patch_pack(img, p):
    n = 0
    i = p.find(ANCHOR)
    while i >= 0:
        lo, hi = i - 0x40, i + 0x600
        for m in re.finditer(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\xfc])+\x00', p[lo:hi]):
            o = lo + m.start(); jb = m.group(0)[:-1]
            if p[o - 1] != 0: continue
            try: jp = jb.decode('cp932')
            except UnicodeDecodeError: continue
            ru, fixed = ru_for(jp)
            if ru is None: continue
            rb = vwf.encode(ru)
            e = o + len(jb)
            while p[e] == 0: e += 1
            cap = len(jb) if fixed else (e - o - 1) & ~1
            assert len(rb) <= cap, (jp, ru, len(rb), cap)
            if fixed: rb += BLANK * ((len(jb) - len(rb)) // 2)
            img.write(img.pack_lba, o, rb + bytes(max(0, len(jb) + 1 - len(rb))) if len(rb) <= len(jb) else rb + b'\0')
            n += 1
        i = p.find(ANCHOR, i + 1)
    return n

# ---- date spot list (phone call: "where shall we go?"): 20-byte records, 16-byte field ----
SPOTS = {'海': 'Море', '山': 'Горы', 'サーカス': 'Цирк', '室内プール': 'Крытый бассейн', 'スタジアム': 'Стадион',
         '遊園地': 'Луна-парк', '動物園': 'Зоопарк', '水族館': 'Океанариум', '映画館': 'Кинотеатр',
         'ボーリング場': 'Боулинг', 'ゲームセンター': 'Игровой зал', 'カラオケＢＯＸ': 'Караоке',
         'ショッピング街': 'Торговая улица', 'タワー': 'Башня', 'スケート場': 'Каток',
         'コンサート会場': 'Концертный зал', '神社': 'Храм', '美術館': 'Музей искусств',
         '植物園': 'Ботанический сад', '中央公園': 'Центральный парк', '河川敷公園': 'Парк у реки'}
SPOTS = lang.tr(SPOTS)
SPOT_ANCHOR = ('海' + '　' * 7).encode('cp932') + b'\0\0\0\0' + '山'.encode('cp932')

def patch_spots(img, p):
    n = 0
    i = p.find(SPOT_ANCHOR)
    while i >= 0:
        o = i
        while True:
            rec = p[o:o + 20]
            if rec[16:20] != bytes(4): break
            try: jp = rec[:16].decode('cp932').rstrip('　')
            except UnicodeDecodeError: break
            if jp not in SPOTS: break
            rb = vwf.encode(SPOTS[jp]); assert len(rb) <= 16, jp
            img.write(img.pack_lba, o, rb + BLANK * ((16 - len(rb)) // 2)); n += 1
            o += 20
        i = p.find(SPOT_ANCHOR, i + 1)
    return n

_patch_profile = patch_pack
def patch_pack(img, p):
    return _patch_profile(img, p) + patch_spots(img, p)

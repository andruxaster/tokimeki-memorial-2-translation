"""EVS creation screen ("SOUND ROOM", disc 1): overlay loaded at 0x800c0000 from CDPACK and
de-obfuscated by the exe (every byte + 0x9c).  Texts are patched in the decoded image and
written back obfuscated.  Kana grids, the banned-reading list and nickname tables are data
for the voice synthesis and stay Japanese.
'^N' = colour code, '\\n' = new line (same notation as exemsg.py)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf, exemsg

KEY = 0x9c
DEC = bytes(((i + KEY) & 255) for i in range(256))
ENC = bytes(((i - KEY) & 255) for i in range(256))
SIG = '１１ブロック以上の空きのあるメモリーカードか、'.encode('cp932')
SIG_OFF = 0x1c59                      # offset of SIG inside the overlay

OWN = {
 'パターン１・・・Ｒ１　パターン２・・・Ｒ２\nパターン３・・・Ｌ１　パターン４・・・Ｌ２':
     'Вариант 1: R1   Вариант 2: R2\nВариант 3: L1   Вариант 4: L2',
 'パターン１・・・Ｒ１　パターン２・・・Ｒ２\nパターン３・・・Ｌ１': 'Вариант 1: R1   Вариант 2: R2\nВариант 3: L1',
 'パターン１・・・Ｒ１　パターン２・・・Ｒ２': 'Вариант 1: R1   Вариант 2: R2',
 '麻生   華澄': 'Касуми', '陽ノ下 光': 'Хикари',
 '苗字': 'Фам.', '名前': 'Имя',
 'ゲームを続けますか？\nはい…^5○^7　いいえ…^3×': 'Продолжить игру?\nДа - ^5○^7   Нет - ^3×',
 'メモリーカードがないとデータを保存できません。\nよろしいですか？　　はい…^5○^7　いいえ…^3×':
     'Без карты памяти сохранить нельзя.\nПродолжить?   Да - ^5○^7   Нет - ^3×',
 'フォーマットされていません。\nフォーマットしますか？　はい…^5○^7　いいえ…^3×':
     'Карта не отформатирована.\nФорматировать?   Да - ^5○^7   Нет - ^3×',
 '終了しました': 'Готово',
 'データを作成中です。しばらくお待ちください': 'Создаю данные. Подождите немного.',
 '残りのＥ．Ｖ．Ｓ．データを作成しますか？': 'Создать остальные данные EVS?',
 '終了しました。再生ボタンで繰り返し聞けます': 'Готово. Повтор - кнопкой «Играть».',
 'Ｅ．Ｖ．Ｓ．サンプルデータを作成しています': 'Создаю пробные данные EVS…',
 'セーブには少し時間がかかります\nしばらくお待ち下さい': 'Сохранение займёт время.\nПодождите немного.',
 'このデータを上書きしてよろしいですか？': 'Записать поверх этих данных?',
 'Ｅ．Ｖ．Ｓ．データを保存しますか？': 'Сохранить данные EVS?',
 'はい': 'Да',
 'このディスクには選ばれた女の子のＥＶＳデータが\n存在しません。選択画面に戻ります。':
     'На этом диске нет данных EVS\nвыбранной девушки. Возврат к выбору.',
 'このディスクはまだ利用できません。\nゲーム中で^5＊ある条件＊^7を満たす必要があります。':
     'Этот диск пока недоступен.\nНужно выполнить в игре ^5*особое условие*^7.',
 '１１ブロック以上の空きのあるメモリーカードか、\nＥＶＳデータの入っているメモリーカードがあれば\n作成したＥＶＳデータを保存することが出来ます。':
     'Данные EVS можно сохранить на карту\nпамяти, где свободно 11 блоков,\nили на карту, где уже есть данные EVS.',
 'の読み方': ': чтение',
}
OWN = lang.tr(OWN)
SKIP = (0xb31, 0x1779)               # banned-reading list (voice data)

def table():
    """Translations: own + the shared memory-card messages from sysui (line by line)."""
    import sysui
    d = {}
    for name in dir(sysui):
        v = getattr(sysui, name)
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(k, str) and isinstance(x, str): d[k] = x
    return d

def to_text(b):
    return b.decode('cp932').replace('\x08', '^') if b'\x08' in b else b.decode('cp932')

def patches(ov):
    """ov: decoded overlay bytes. Returns [(offset, new_bytes)] in decoded space."""
    shared = table(); out = []
    for m in re.finditer(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\xfc]|\x08[0-9]|\n|[ -~])+\x00', ov[:0x30000]):
        o = m.start(); jb = m.group(0)[:-1]
        if SKIP[0] <= o < SKIP[1]: continue
        try: jp = jb.decode('cp932')
        except UnicodeDecodeError: continue
        jp = jp.replace('\x085', '^5').replace('\x087', '^7').replace('\x083', '^3')
        ru = OWN.get(jp)
        if ru is None:
            parts = [shared.get(x) for x in jp.split('\n')]
            if len(jp) >= 3 and all(parts): ru = '\n'.join(parts)
        if ru is None: continue
        # the string may start right after a non-zero byte (pointer tables): find its true start
        e = o + len(jb)
        while e < len(ov) and ov[e] == 0: e += 1
        cap = e - o - 1
        rb = exemsg.enc(ru, True)
        if len(rb) > cap: print('EVS too long', len(rb), cap, ru); continue
        out.append((o, rb + bytes(e - o - len(rb))))
    return out

def patch_pack(img, p):
    i = p.find(SIG.translate(ENC))
    if i < 0: return 0
    base = i - SIG_OFF
    ov = p[base:base + 0x30000].translate(DEC)
    ps = patches(ov)
    for o, b in ps: img.write(img.pack_lba, base + o, b.translate(ENC))
    return len(ps)

if __name__ == '__main__':
    p = open(sys.argv[1], 'rb').read()
    i = p.find(SIG.translate(ENC)); ov = p[i - SIG_OFF:i - SIG_OFF + 0x30000].translate(DEC)
    for o, b in patches(ov): print(hex(0x800c0000 + o), len(b))

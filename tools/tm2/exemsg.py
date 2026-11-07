"""System messages inside the main executable (SLPM): disc check / disc swap, append disc,
mouse/controller notices, EVS creation help.  '^N' = colour code (0x08 'N'), '\\n' = new line,
spaces at the start of a line are kept as ASCII spaces (alignment)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import lang
import sys, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import vwf

MSG = [
 ('\n     決定ボタン：華澄か光のＥＶＳを作成', '\n     Кнопка ввода: EVS Касуми/Хикари'),
 ('\n             キャンセルボタン：戻る', '\n             Отмена: назад'),
 ('^3ディスクをチェックしています。\n^7少々、お待ちください・・・。', '^3Проверка диска.\n^7Подождите, пожалуйста…'),
 ('\n      ^4○^7ボタン：華澄か光のＥＶＳを作成', '\n      ^4○^7: EVS Касуми или Хикари'),
 ('華澄と光以外のＥＶＳデータを作成する場合は、\n', 'Для EVS не Касуми и не Хикари:\n'),
 ('\n              ^3×^7ボタン：キャンセル', '\n              ^3×^7: отмена'),
 ('^3ディスクがセットされていません。^7', '^3Диск не вставлен.^7'),
 ('^3ディスクが違います。', '^3Это не тот диск.'),
 ('^7ときめき２の^6\n', '^7Токимеки 2:^6\n'),
 ('^7をセットしてください。', '^7 - вставьте, пожалуйста.'),
 ('新規^6【アペンドディスク】^7を認識しました。', 'Найден новый ^6【Доп. диск】^7.'),
 ('^7又は、^6\n', '^7или^6\n'),
 ('これから始まるミニゲームは^3マウス^7での操作ができません。\n', 'В этой мини-игре ^3мышь^7 не работает.\n'),
 ('^3コントローラ端子２^7の^3コントローラ^7で操作するか、\n', 'Играйте ^3контроллером^7 в ^3порту 2^7\n'),
 ('^3マウス^7を^3コントローラ^7に接続しなおしてください。', 'или замените ^3мышь^7 на ^3контроллер^7.'),
 ('操作を^3コントローラ端子１^7に戻します。\n^3コントローラ端子１^7の^3', 'Управление снова на ^3порту 1^7.\nВозьмите ^3'),
 ('コントローラ', 'контроллер'),
 ('^7に持ち替えて\n何かボタンを押してください。', '^7 порта 1\nи нажмите любую кнопку.'),
]
MSG = lang.tr(MSG)

TOK = re.compile(r'(\^\d|\n *)')

def enc(s, russian):
    out = b''
    for part in TOK.split(s):
        if not part: continue
        if part[0] == '^': out += b'\x08' + part[1].encode()
        elif part[0] == '\n': out += part.encode()
        else: out += vwf.encode(part) if russian else part.encode('cp932')
    return out

def patches(exe):
    """exe: bytes of the executable (file offsets). Returns [(offset, bytes)]."""
    out = []
    for jp, ru in MSG:
        jb = enc(jp, False)
        o = exe.find(jb + b'\0')
        while o >= 0 and not (o % 4 == 0 or exe[o - 1] == 0): o = exe.find(jb + b'\0', o + 1)
        assert o >= 0, jp
        e = o + len(jb)
        while exe[e] == 0 and e < len(exe) - 1: e += 1
        cap = e - o - 1
        rb = enc(ru, True)
        assert len(rb) <= cap, (ru, len(rb), cap)
        out.append((o, rb + bytes(e - o - len(rb))))
    return out

if __name__ == '__main__':
    exe = open(sys.argv[1], 'rb').read()
    for o, b in patches(exe): print(hex(o), len(b))

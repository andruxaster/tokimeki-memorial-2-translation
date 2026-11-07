"""Target language of the build: TM2_LANG=ru (default) or en.

UI strings are written in Russian inside the modules; for an English build they are
mapped through lang/en_ui.tsv (Russian -> English).  `tr(obj)` maps every string in a
dict / list / tuple that contains Cyrillic; a missing entry is an error."""
import os, re
LANG = os.environ.get('TM2_LANG', 'ru')
EN = LANG == 'en'
HERE = os.path.dirname(os.path.abspath(__file__))
# project root (tr/, tr_en/, work/ live there); default: two levels above tools/tm2
ROOT = os.environ.get('TM2_ROOT', os.path.dirname(os.path.dirname(HERE)))
CYR = re.compile('[А-Яа-яЁё]')
_tab = None
FW = str.maketrans('０１２３４５６７８９', '0123456789')

def table():
    global _tab
    if _tab is None:
        _tab = {}
        p = os.path.join(HERE, 'lang', 'en_ui.tsv')
        if os.path.exists(p):
            for ln in open(p, encoding='utf-8'):
                ln = ln.rstrip('\n')
                if not ln or ln.startswith('#') or '\t' not in ln: continue
                ru, en = ln.split('\t', 1)
                _tab[ru.replace('\\n', '\n')] = en.replace('\\n', '\n')
    return _tab

def t(s):
    if not EN or not isinstance(s, str) or not CYR.search(s): return s
    tab = table()
    if s in tab: return tab[s]
    # templates with %s: '【Доп. диск %s】' also covers '【Доп. диск １】' (full-width digits -> ASCII)
    for k, v in tab.items():
        if '%s' in k and v.count('%s') == k.count('%s'):
            m = re.fullmatch(re.escape(k).replace('%s', '(.+?)'), s)
            if m: return v % tuple(g.translate(FW) for g in m.groups())
    raise KeyError('no English for: %r' % s)

def tr(obj):
    if not EN: return obj
    if isinstance(obj, str): return t(obj)
    if isinstance(obj, dict): return {k: tr(v) for k, v in obj.items()}
    if isinstance(obj, list): return [tr(v) for v in obj]
    if isinstance(obj, tuple): return tuple(tr(v) for v in obj)
    return obj

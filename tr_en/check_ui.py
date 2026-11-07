"""check_ui.py : checks tools/tm2/lang/en_ui.tsv against ui_src.tsv
(every Russian string translated; English not longer in bytes than the Russian)."""
import os as _o; _ROOT = _o.environ.get('TM2_ROOT', _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
import os, sys
os.environ['TM2_LANG'] = 'en'
sys.path.insert(0, _ROOT + '/tools/tm2'); import exemsg, re
src = {}
for l in open(_ROOT + '/tr_en/ui_src.tsv', encoding='utf-8'):
    if l.startswith('#'): continue
    m, jp, ru, n = l.rstrip('\n').split('\t'); src[ru] = (m, int(n))
en = {}
for l in open(_ROOT + '/tools/tm2/lang/en_ui.tsv', encoding='utf-8'):
    l = l.rstrip('\n')
    if not l or l.startswith('#'): continue
    ru, e = l.split('\t', 1); en[ru] = e
bad = 0
for ru, (m, n) in src.items():
    if ru not in en: print('MISSING', m, ru); bad += 1; continue
    e = en[ru]
    if re.search('[А-Яа-яЁё]', e): print('CYRILLIC', e); bad += 1; continue
    if ru.count('\\n') != e.count('\\n'): print('LINES differ', ru, '|', e); bad += 1; continue
    if ru.count('^') != e.count('^'): print('COLOR CODES differ', ru, '|', e); bad += 1; continue
    k = len(exemsg.enc(e.replace('\\n', '\n'), True))
    if n >= 0 and k > n: print('TOO LONG %d>%d' % (k, n), m, e); bad += 1
print('checked %d, %d problems' % (len(src), bad))

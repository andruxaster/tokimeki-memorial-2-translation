"""check_plain.py out.tsv : checks plain-string translations (byte limits per line and total)."""
import os as _o; _ROOT = _o.environ.get('TM2_ROOT', _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
import os, sys, json
os.environ['TM2_LANG'] = 'en'
sys.path.insert(0, _ROOT + '/tools/tm2'); import vwf, plainapply
idx = json.load(open(_ROOT + '/work/plain_index.json'))
jp_by = {v: k for k, v in idx['ids'].items()}
def enc(ru):
    return b'\n'.join(vwf.encode(l) for l in ru.split('|'))
bad = 0; n = 0
for ln in open(sys.argv[1], encoding='utf-8'):
    ln = ln.rstrip('\n')
    if not ln or ln.startswith('#') or '\t' not in ln: continue
    i, ru = ln.split('\t', 1); i = int(i); n += 1
    jp = jp_by[i]
    if ru == '=': continue
    import re as _re
    if _re.search('[А-Яа-яЁё]', ru): print(i, 'CYRILLIC', ru); bad += 1; continue
    jl = jp.split('\n'); rl = ru.split('|')
    try: b = plainapply.enc(jp, ru)
    except Exception as e: print(i, 'BAD CHAR', e, ru); bad += 1; continue
    if len(rl) != len(jl): print(i, 'LINES %d != %d' % (len(rl), len(jl)), ru); bad += 1; continue
    for a, r in zip(jl, rl):
        lim = len(a.lstrip(' ').encode('cp932')); lb = len(vwf.encode(r.lstrip(' ')))
        if lb > max(lim, 2): print(i, 'LINE TOO LONG %d > %d' % (lb, lim), r); bad += 1; break
    else:
        if len(b) > idx['caps'][jp]: print(i, 'TOTAL TOO LONG %d > %d' % (len(b), idx['caps'][jp]), ru); bad += 1
print('checked %d lines, %d problems' % (n, bad))

#!/usr/bin/env python3
"""Check a translation output file.  usage: check.py out_XX.tsv
Each line: id<TAB>russian.  Reports lines that do not fit, bad tokens, bad chars."""
import os as _o; _ROOT = _o.environ.get('TM2_ROOT', _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
import sys, json, re
sys.path.insert(0, _ROOT + '/tools/tm2')
import vwf, lines
idx = json.load(open(_ROOT + '/tr/index.json'))
jp_by_id = {v: k for k, v in idx['tid'].items()}
bad = 0; n = 0
for ln in open(sys.argv[1], encoding='utf-8'):
    ln = ln.rstrip('\n')
    if not ln.strip() or ln.startswith('#'): continue
    try:
        i, ru = ln.split('\t', 1); i = int(i)
    except ValueError:
        print('FORMAT:', ln); bad += 1; continue
    n += 1
    jp = jp_by_id.get(i)
    if jp is None: print('UNKNOWN ID', i); bad += 1; continue
    cap = idx['caps'][jp]
    if lines.tokens(jp) != lines.tokens(ru):
        print('%d TOKENS differ: jp=%s ru=%s' % (i, jp, ru)); bad += 1; continue
    try:
        b = lines.template_bytes(ru, vwf.encode)
    except Exception as e:
        print('%d BAD CHAR (%s): %s' % (i, e, ru)); bad += 1; continue
    if len(b) > cap:
        print('%d TOO LONG %d>%d bytes (уберите ~%d букв): %s' % (i, len(b), cap, len(b) - cap, ru)); bad += 1
print('checked %d lines, %d problems' % (n, bad))

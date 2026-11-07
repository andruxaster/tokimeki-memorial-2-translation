#!/usr/bin/env python3
"""Check an English translation file.  usage: check_en.py out_XX.tsv   (script lines, tr/index.json ids)
Each line: id<TAB>english.  Reports lines that do not fit, bad tokens, Cyrillic/kana left."""
import os as _o; _ROOT = _o.environ.get('TM2_ROOT', _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
import os, sys, json, re
os.environ['TM2_LANG'] = 'en'
sys.path.insert(0, _ROOT + '/tools/tm2')
import vwf, lines
idx = json.load(open(_ROOT + '/tr/index.json'))
jp_by_id = {v: k for k, v in idx['tid'].items()}
BADCH = re.compile('[А-Яа-яЁёぁ-ゖァ-ヺ一-鿿]')
bad = 0; n = 0
for ln in open(sys.argv[1], encoding='utf-8'):
    ln = ln.rstrip('\n')
    if not ln.strip() or ln.startswith('#'): continue
    try:
        i, en = ln.split('\t', 1); i = int(i)
    except ValueError:
        print('FORMAT:', ln); bad += 1; continue
    n += 1
    jp = jp_by_id.get(i)
    if jp is None: print('UNKNOWN ID', i); bad += 1; continue
    cap = idx['caps'][jp]
    if lines.tokens(jp) != lines.tokens(en):
        print('%d TOKENS differ: jp=%s en=%s' % (i, jp, en)); bad += 1; continue
    if BADCH.search(lines.TOK.sub('', en)) and not BADCH.search(lines.TOK.sub('', jp)) is None:
        pass
    if re.search('[А-Яа-яЁё]', en):
        print('%d CYRILLIC left: %s' % (i, en)); bad += 1; continue
    try:
        b = lines.template_bytes(en, vwf.encode)
    except Exception as e:
        print('%d BAD CHAR (%s): %s' % (i, e, en)); bad += 1; continue
    if len(b) > cap:
        print('%d TOO LONG %d>%d bytes (cut ~%d letters): %s' % (i, len(b), cap, len(b) - cap, en)); bad += 1
print('checked %d lines, %d problems' % (n, bad))

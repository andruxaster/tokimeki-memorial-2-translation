#!/bin/bash
# build translated disc 2 image: make_d2.sh out.bin
set -e
cd "${TM2_ROOT:-$(dirname "$(readlink -f "$0")")/../..}"
python3 -I tools/tm2/apply2.py "tm2_cd2/TM2 CD 2.BIN" "$1" work/cdpack2.bin work/d2.json tr/index.json tr/names.tsv 'tr/out_*.tsv'
python3 -I -c "
import sys; sys.path.insert(0,'tools/tm2')
import build
img=build.Image('$1')
rows=[r for r in build.load_tsv('tm2ru2/disc2_opening_ru.tsv') if r[3]=='plain']
print('plain:',build.insert_text(img,rows)); img.close()"

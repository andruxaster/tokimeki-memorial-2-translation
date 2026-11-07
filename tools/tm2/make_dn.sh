#!/bin/bash
# build translated disc N (2..5): make_dn.sh N out.bin     (TM2_LANG=en for the English build)
set -e
cd "${TM2_ROOT:-$(dirname "$(readlink -f "$0")")/../..}"
N=$1
if [ "$TM2_LANG" = en ]; then TR=tr_en; OPEN=tr_en/disc2_opening_en.tsv; else TR=tr; OPEN=tm2ru2/disc2_opening_ru.tsv; fi
case $N in 2) SRC="tm2_cd2/TM2 CD 2.BIN"; PACK=work/cdpack2.bin;; *) SRC="tm2_cd$N/TM 2 CD $N.BIN"; PACK=work/cdpack$N.bin;; esac
PLAIN_DISC=$N python3 -I tools/tm2/apply2.py "$SRC" "$2" $PACK work/d$N.json tr/index.json tr/names.tsv "$TR/out_*.tsv"
if [ "$N" = 2 ]; then python3 -I -c "
import sys; sys.path.insert(0,'tools/tm2')
import build
img=build.Image('$2')
rows=[r for r in build.load_tsv('$OPEN') if r[3]=='plain']
print('plain:',build.insert_text(img,rows)); img.close()"; fi

#!/bin/bash
# build translated disc 1: make_d1.sh out.bin     (TM2_LANG=en for the English build)
set -e
cd "${TM2_ROOT:-$(dirname "$(readlink -f "$0")")/../..}"
if [ "$TM2_LANG" = en ]; then TR=tr_en; PRO=tr_en/prologue_en.tsv; else TR=tr; PRO=tm2ru2/prologue_ru2.tsv; fi
PLAIN_DISC=1 SHORT_FROM=0x3000000 python3 -I tools/tm2/apply2.py "tm2_in/TM 2 CD 1.BIN" "$1" work/cdpack.bin work/d1.json tr/index.json tr/names.tsv "$TR/out_*.tsv"
python3 -I -c "
import sys; sys.path.insert(0,'tools/tm2')
import build
img=build.Image('$1')
e=build.insert_text(img,build.load_tsv('$PRO'))
print('prologue rows: %d not applied (already translated)'%len(e)); img.close()"

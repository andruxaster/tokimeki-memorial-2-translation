# Tokimeki Memorial 2 (PS1) — English and Russian fan translation

Fan translation of **Tokimeki Memorial 2** (ときめきメモリアル2, Konami, 1999) for the PlayStation,
Konami The Best edition, 5 discs (SLPM-86355…). Two complete language versions are provided as
PPF patches:

| | English | Russian |
|---|---|---|
| Patches | `patches/en/TM2_EN_disc1..5.ppf` | `patches/ru/TM2_RU_disc1..5.ppf` |
| Script | 36 687 unique lines (`tr_en/out_*.tsv`) | same (`tr/out_*.tsv`) |
| Non-script text | 1 841 strings (`tr_en/plainout_*.tsv`) | same (`tr/plainout_*.tsv`) |
| UI / menus / graphics | `tools/tm2/lang/en_ui.tsv` | built into the tool modules |

No game data is distributed: you need your own dumps of the five discs.

## Applying the patches
1. Dump your discs as BIN/CUE (MODE2/2352, one track). The patches were made against these images:

   | Disc | Size (bytes) | MD5 |
   |---|---|---|
   | 1 | 692447616 | bdb4628430b087b84f1a94e523ee7206 |
   | 2 | 739793376 | 960bf8984e14537ae8d6348bb60ca468 |
   | 3 | 747917184 | 51f5fb6e350c1986a454e199fc0b1bf5 |
   | 4 | 745115952 | 40e9f086a5619047e2937c894a68bd2c |
   | 5 | 743427216 | 69b456f6f9ef1cab906eea1ab393cfdd |

2. Apply `TM2_EN_discN.ppf` (or `TM2_RU_discN.ppf`) to disc N with any PPF 3.0 tool
   (PPF-O-Matic, ApplyPPF, `ppfdev`…). Each disc has its own patch.
3. Play in an emulator or burn. When the game asks for the next disc, insert the patched one.

## What is translated
- The whole scenario on all 5 discs: childhood (disc 1), three school years, dates, events, endings.
- Speaker labels, names and forms of address inserted by the game, the hero's name entry
  (Latin / Cyrillic letters, two letters per cell).
- Calendar and dates (`24.05.1999 (Mo)`), status panel, clubs, phone menu,
  Takumi's notebook, date spots, memory-card and file-select screens, options, title menu,
  graphic buttons, disc-swap and system messages in the executable, EVS creation screen.
- Mini-game texts, endings and credits, songs, album, PocketStation messages (plain SJIS strings).

A narrow 8-px font is injected: every 16-px text cell shows two letters, so lines keep their
original byte length and no pointers have to be moved.

## Known limitations
- The translation was produced with AI assistance and has not been fully proofread. Some identical
  Japanese lines are reused in different scenes with one translation, so a join between lines can
  occasionally read awkwardly. Corrections are welcome (see below).
- EVS (the voice system that says the hero's name) still uses kana input for the *reading* of the
  name: the voice is assembled from Japanese syllables. A few EVS screen graphics ("ノコリNモジ",
  the N@/OK buttons) are still Japanese.
- English build: tested in an emulator through the title, file select, name entry and the
  childhood chapter on disc 1 and booting discs 2–3. Later scenes were checked only by the length
  and token checker, not on screen.

## Repository layout
```
patches/        ready PPF patches (en, ru)
tr/             Russian: script batches (batch_XX.txt, Japanese + context), translations out_XX.tsv,
                plain strings plain_XX.txt / plainout_XX.tsv, guides and checkers, index.json
tr_en/          English: out_XX.tsv, plainout_XX.tsv, GUIDE_EN.md (style + glossary), checkers,
                prologue_en.tsv / disc2_opening_en.tsv (fixed-offset rows)
tm2ru2/         Russian fixed-offset rows (prologue, disc 2 opening)
work/           build data: line offsets per disc (d1..d5.json), plain string index
tools/tm2/      build tools (Python 3, needs keystone-engine, Pillow, numpy)
tools/c/        small C helpers used while researching the compression formats
```

## Building from source
Requirements: Python 3.10+, `pip install keystone-engine pillow numpy`.

1. Put your original images at the paths the scripts expect (relative to the repo root):
   `tm2_in/TM 2 CD 1.BIN`, `tm2_cd2/TM2 CD 2.BIN`, `tm2_cd3/TM 2 CD 3.BIN`,
   `tm2_cd4/TM 2 CD 4.BIN`, `tm2_cd5/TM 2 CD 5.BIN`.
2. Extract the data pack of each disc:
   ```
   python3 tools/tm2/getfile.py "tm2_in/TM 2 CD 1.BIN" CDPACK00.BIN work/cdpack.bin
   python3 tools/tm2/getfile.py "tm2_cd2/TM2 CD 2.BIN" CDPACK00.BIN work/cdpack2.bin
   # ... same for discs 3-5 -> work/cdpack3.bin .. work/cdpack5.bin
   ```
3. Build:
   ```
   TM2_LANG=en bash tools/tm2/make_d1.sh out/en1.bin          # disc 1
   TM2_LANG=en bash tools/tm2/make_dn.sh 2 out/en2.bin        # discs 2..5
   bash tools/tm2/make_d1.sh out/ru1.bin                      # Russian (default)
   python3 tools/tm2/mkppf.py original.bin out/en1.bin TM2_EN_disc1.ppf
   ```
   Build discs one at a time (each build loads the whole data pack into memory).

## Editing the translation
- Script: `tr_en/out_XX.tsv` is `id<TAB>text`; the Japanese source and context are in
  `tr/batch_XX.txt`. Check a file with `python3 tr_en/check_en.py tr_en/out_XX.tsv` — it verifies
  the byte limit of every line and that all `{xx}` tokens are kept. Rules and glossary:
  `tr_en/GUIDE_EN.md`.
- Plain strings: `tr_en/plainout_XX.tsv`, check with `tr_en/check_plain_en.py`.
- UI: `tools/tm2/lang/en_ui.tsv` maps the Russian UI strings of the tool modules to English
  (`tr_en/check_ui.py`).

## Credits
Translation and tools: andruxaster, with Claude (Anthropic). Tokimeki Memorial 2 © 1999 Konami.
This is a non-commercial fan project; it contains no game data.

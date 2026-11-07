# Tokimeki Memorial 2 (PS1) — English translation guide

The game is a high-school dating sim. The hero (the player) attends Hibikino High and spends three
years with the girls and his friends. Tone: natural, lively conversational English, like a good fan
localization of an anime — keep each character's voice (see glossary). Not stiff, not over-localized.

## Input
You get two files per batch:
- `tr/batch_XX.txt` — the Japanese script (format below);
- `tr/out_XX.tsv` — the finished **Russian** translation of the same ids (`id<TAB>russian`).
  Use it as a reference for meaning, context and line splits, but translate from the **Japanese**;
  if the two disagree, the Japanese wins.

`batch_XX.txt` format:
```
### SCENE n
  [speaker: 白雪]            <- who speaks next (label from the script)
123	26	Japanese line           <- id, byte limit, text
ctx	-	Japanese line	=> перевод <- context only (translated elsewhere) — do NOT output it
```
One entry = one line of the dialogue window. A message is usually 1–3 consecutive lines: translate
the message as a whole, but lay it out over the same lines (each line is its own id). If an id appears
several times, translate it once.

## Output: `tr_en/out_XX.tsv`
UTF-8, one line per id: `id<TAB>english`. Only numeric ids of YOUR batch, every one of them.

## Length limit (important)
Narrow characters take 1 byte each (two of them share one 16-px cell):
`a-z A-Z 0-9 space . , ! ? - : … " ( ) ' /`
Everything else (「」『』～♪&%, Japanese characters) is a full cell = 2 bytes. Tokens `{xx}` are 1–2 bytes.
The limit (2nd column) is in bytes ≈ maximum number of English characters.
Check yourself: `python3 tr_en/check_en.py tr_en/out_XX.tsv` — every line must
pass. If something does not fit, rephrase shorter (don't just chop words).

## Tokens {xx}
Substitutions — keep ALL of them, in the same order (the checker verifies this):
- {1d} player's family name, {1e} player's given name, {1f} player's nickname;
- {10}…{1c}, {20}…{2d} — a name or form of address inserted by the game (e.g. in 「{21}を待とう）」 it is
  the girl we are waiting for). Build the sentence so the inserted name reads naturally.
- {2e:xx}, {2f:xx}, {3x:xx}, {0c} — control codes (pause, sound, "continue on the same line"); keep in place.
  A line ending in {0c} is continued by the next line on screen (e.g. "Let's go, " + "{1e}!").

## Style
- Hero's thoughts end with ）(opened by （ on an earlier line) — keep the parentheses: ( … ).
- Answer choices in 『』 — keep 『』 (2 bytes each).
- 「……」 → "…". Stretched words with ～ → spell it out ("Heeey!"); ～ costs 2 bytes.
- Numbers: digits are fine (1 byte each).
- No Japanese honorifics in narration/dialogue except where they carry meaning: keep "-senpai" for
  juniors addressing seniors, "-sensei" for teachers is fine as "Ms. Aso"/"Mr. …" depending on context.
  Mei's servants call her "Lady Mei"/"Mistress".
- Do not use characters outside the set: no — – “ ” ‘ ’ (use - " ').

## Glossary (Western name order; in dialogue people mostly use given names)
Hikari Hinomoto (陽ノ下光) — the hero's childhood friend, cheerful, sporty.
Miho Shirayuki (白雪美帆) — dreamy, into fortune-telling and fairies; her twin sister Maho Shirayuki (白雪真帆).
Kaedeko Sakura (佐倉楓子) — gentle, from the countryside. Miyuki Kotobuki (寿美幸) — clumsy, unlucky, "Miyu".
Homura Akai (赤井ほむら) — tomboyish student council president. Kaori Yae (八重花桜梨) — quiet, aloof.
Akane Ichimonji (一文字茜) — works part-time jobs, sharp-tongued. Kotoko Minazuki (水無月琴子) — traditional, proper.
Mei Ijuin (伊集院メイ) — arrogant rich girl, speaks pompously ("…のだ"), calls everyone 貴様 ("you, commoner"/"peasant").
Takumi Sakaki (坂城匠) — the hero's best friend, info broker. Junichiro Hokari (穂刈純一郎) — "Jun", sporty friend.
Maika Kudanshita (九段下舞佳). Sumire Nozaki (野咲すみれ). Kasumi Aso (麻生華澄) — teacher, the hero's old neighbor.
Hibikino High (ひびきの高校), Hibikino (town), Ijuin Bridge (伊集院大橋), Central Park (中央公園), Hibikino Station
(ひびきの駅), the station square (駅前広場), the shrine (神社). おやぢ — "Pops" (the shopkeeper).
番長 — gang boss / "Boss" (school delinquent leaders); 総番長 — the Big Boss.
マルハゲドン — the movie "Maruhageddon". Clubs: 吹奏楽部 brass band, 陸上部 track & field, 野球部 baseball,
サッカー部 soccer, テニス部 tennis, バスケ部 basketball, 美術部 art club, 茶道部 tea ceremony club, 演劇部 drama club.
Hero's stats: 体調 Condition, 文系 Humanities, 理系 Sciences, 芸術 Arts, 運動 Athletics, 雑学 Trivia,
容姿 Looks, 根性 Guts, ストレス Stress. EVS — the system that lets the girls say the hero's name.
Childhood: 超戦士ドラゴンチョコ "Super Warrior Dragon Choco" (a candy); かすみおねーちゃん "Big Sis Kasumi".
Speaker labels in this game: Hikari, Miho, Maho, Kaede(ko), Miyuki, Homura, Kaori, Akane, Kotoko, Mei, Takumi, Jun,
Kasumi (teacher; "Aso" in childhood).

## Consistency notes (from finished batches)
- Name tokens: {22} Hikari, {23} Kotoko, {24} Miyuki, {25} Akane, {26} Miho, {27} Homura, {28} Kaori, {29} Kaede, {2a} Mei.
- Miyuki calls herself "Miyu" (third person). Homura = "prez". Mei calls the hero "peasant".
- 合宿 "training camp", 花火大会 "the fireworks", 河川敷公園 "the river park", 文化祭 "the school festival", 肝試し "the scare walk".
- Impression lines: "Looks like I made a great impression!)", "Seems I made a good impression)", "Bad impression, huh…)".
- Self-introduction keeps family name first: "I'm {1d} {1e}."
- Helper scripts: use your OWN subfolder of the scratchpad (other translators run in parallel).

# `raven` Experiment Log

Same conventions as `../simple/log.md`: newest entries at the top, every run
logged, traces under `traces/` at the repo root.

---

## 2026-09-22 (later) -- GUI: use the Mod-3-4 decks (`K2 ??+ ****`, arithmetic check)

After the character fix, the GUI loaded and trained, then punched one card `K2 ??+
****` and halted with an arithmetic check. That is the **Punch-Check symptom of the
original interpreter** (TNF odd-address bug: numeric/type fields print as `??+`) --
Jeff was loading the *original* decks. Reproduced in the CLI: original Deck-1/Deck-2
give `K2 ??+ ****`, `V1 ??+ +ONCE`, ...; the **Mod-3-4** decks print correctly. All my
runs (`traces/runraven.sh`) always used Mod-3-4 but I never told Jeff. Note: the
original decks also print `TYPE9 + 3 OVERLAP` at load, so the first GUI error report was
probably at least partly the unpatched deck, not only the `:` characters -- both fixes
are needed. Wrote `raven/README.txt` with the exact deck order.

---

## 2026-09-22 -- GUI hang: invalid card characters in comments (`:` `;` `<` `>` `[` `]` `'` and lowercase)

Jeff, running `rave.ipl` in the browser GUI: `TYPE9 + 3 OVERLAP` on the title card,
then a hang "compiling the J60 right after A0" (also not a memory-size problem: same at
40K and 60K). Not reproduced by the CLI, because the CLI card reader silently passes
characters the GUI reader rejects. The GUI's `CardReader.invalidCharRex` allows only
`A-Z 0-9 space . ) + $ * - / , ( = @ | } ! " ]` (uppercase only). My generated
comments used `:` (`RAVEN4: ...`, `J60: (0) = ...` -- exactly the card that hung),
plus `;` `<` `>` `[` `]` `'` and a lowercase `n`.

**Fix:** `mkdeck.py` now uppercases comment text and turns any other character into a
space (`card()` and `const()`); `raven4.ipl`/`rave.ipl` regenerated and re-verified in
the CLI (0 traps, identical output). **CLI now warns** when any loaded card contains a
character the GUI reader would reject (`run1620.mjs`, `WARNING: file:line: invalid card
character(s)`). Older probe files (`raven2*`, `raven3`, `raven4a-c`, `raven5a`, `simple7`,
`hold_8`) still contain `:` etc.; they run in the CLI but not in the GUI. Not confirmed on
the actual GUI (no access) -- pending Jeff's test.

---

## 2026-09-21 (later still) -- `rave.ipl`: same program without the type-1 comment cards

`mkdeck.py --no-comments --out=rave.ipl` (new flags; `--out` defaults to
`raven4.ipl`). Comments (type-1 cards) are ignored by the loader, so the program
is identical: 867 cards instead of 1078 (211 fewer, 20%). Verified same behavior:
0 traps, clean halt, byte-identical generated text and table. **Headless CLI run
time is barely different (30.3 s vs 31.3 s)** because the time is dominated by
executing the program (train + 100 steps + table), not by reading cards; the saving
matters for the real-time card reader in the browser UI. Regenerate with
`python3 mkdeck.py [nlines] [steps] --no-comments --out=rave.ipl`.

---

## 2026-09-21 (later) -- full words instead of 4-letter abbreviations

An alphanumeric data term holds only 5 chars, so each word is now a **list of
pieces**: flag char + up to 4 letters (`+` first piece, `-` continuation), e.g.
*pondered* = `+POND`, `-ERED`. `mkdeck.py` emits piece terms `V1..Vp`
(region `V0`), one piece list `Yk` per word (region `Y0`), and `X3` = the piece
lists in vocabulary order. Phase 0 now maps word `Tk` -> `Yk` on the `X4` map
(same `J11` loop). New routine **`G4`** prints a word: it takes the piece list on
the stack, walks it (`J60`/`J80`, cell in `W7`) and `J152`-prints each piece.
The three inline `J10`+`J152` sequences (first word, `G1`, `G3` x2) became
`J10` + `G4`. `decode.py` starts a word at each `+` piece and joins `-` pieces.
Routine region `G0` grew to 6 (`G1`-`G4`). Non-letters are stripped from the
printed text (`'tis` -> TIS).

**Result** (12 lines, 100 steps, `L0`=900, default 40000 digits, 1078 cards): 0
traps, clean halt, fits. Table rows like `I : PONDERED 1, NODDED 1, MUTTERED 1,
REMEMBER 1, WISHED 1, HAD 1`; generated: *ONCE UPON A MIDNIGHT DREARY WHILE I
MUTTERED TAPPING AT MY BOOKS SURCEASE OF SOME VISITER I HAD SOUGHT TO BORROW FROM
MY CHAMBER DOOR ONLY THIS AND EACH SEPARATE DYING EMBER WROUGHT ITS GHOST UPON THE
FLOOR EAGERLY I NODDED NEARLY NAPPING SUDDENLY THERE CAME A TAPPING AS OF FORGOTTEN
LORE ...* (`raven4_decoded.txt`).

---

## 2026-09-21 -- two stanzas, continuation table, and the "trap" was J16 (correction)

**Scaled to 12 lines** (2 stanzas): 115 tokens, 83 distinct words, 100 generated
steps, list region `L0` = 900 cells, **runs at the default 40000 digits** (700
also works; `L0` = 1100 does NOT fit in 40000 digits -- 724 traps, never finishes;
1500 works with `--memory 60000`). Defaults in `mkdeck.py` are now `12 100 --lspace=900`.

**Continuation table.** New routine `G3` (called per word from a table loop over
vocabulary list `X2`; on by default, `--no-table` to omit) prints, one card each,
the word text then every successor's text and count, with `****` separator cards.
`decode.py run.log` turns the punched cards into the readable table plus the
generated text; a saved result is `raven4_decoded.txt` (85 table rows, e.g.
`WHIL : I 2`, `AT : MY 2`, `MY : CHAM 2, BOOK 1`, `THE : ...`). All 100 generated
transitions verified to exist in the table.

**Correction to the previous entry.** The "TRAPPED ON 00001/00003" was NOT list-space
exhaustion. It came from `J16`: it tests every attribute's value as a number, and
the `K1` attribute (word -> alphanumeric text term) stored on each word's
description list is non-numeric, so **every `J16` call trapped twice** (harmless to
the output but it leaks). This had been present since the K1 change (the pushed
commit d04319a traps 2x per step; I had filtered the log with `grep " 81 "` and
missed it). Fix: the word -> text map now lives on **one separate describable list
`X4`** (attribute = word `Tn`, value = text term `Vn`; lookup = `J10` on `X4`), so
successor description lists contain only numeric counts. Result: **0 traps**, and the
cat test that died at ~79 steps now runs all 300 steps with `L0` = 300.
So bug 2 (unrestored `W0`-`W2`) is still real but is *not* what limited generation
length; it is worked around (variables in `W4`-`W9`).

Other changes: support lists renamed `X1` (text), `X2` (words), `X3` (text terms),
`X4` (map) so the vocabulary can exceed 36; `T0`/`V0` sized to vocabulary + 2.

---

## 2026-09-20 (verification) -- do the counts really drive generation? Yes; but generation traps after ~80 steps

Two-line corpus had no repeated bigram (all counts 1), so the increment path
and the weighting were not exercised. Test corpus (scratch copy of
`mkdeck.py` with a custom `raven.txt`): *the cat sat on the mat the cat ran the
cat sat*, 300 steps, `--table`. **Trained table exactly right:** the->cat 3,
the->mat 1, cat->sat 2, cat->ran 1, sat->on 1, sat->the 1 (wrap), on/mat/ran->the
1. **Sampling follows the counts** (79 steps): the->cat 19 vs the->mat 9
(expect 3:1), cat->sat 10 vs cat->ran 8 (expect 2:1).

**Problem:** after ~79 generated words the run hits `TRAPPED ON 00003` (error
trap, repeats forever). Consistent with **list-space exhaustion from bug 2** (the
library routines' unbalanced preserve/restore leaks ~2-3 pushdown cells per
`J16`/`J10` call; region `L0` = 200 cells). So generation length is currently
bounded by `L0`, and core (40000 digits, 12 per cell) limits how far `L0` can
grow. Not yet confirmed as the cause (would need `H2` monitored).

---

## 2026-09-20 (later) -- `raven4.ipl` now prints WORDS (4-letter abbreviations), not `T###`

Jeff's compromise: give each word a 4-letter abbreviation and print that.
`mkdeck.py` derives abbreviations (first 4 letters, made unique by
`first3+digit` on collision; recorded as `T# ABBR word` in `raven4.vocab`) and
emits, per word, an alphanumeric data term `Vn` (PQ=21, up to 5 chars in the
SYMB field). Symbols stay `Tn`; the program attaches each text term to its word
as attribute `K1` (`J11`, phase 0, loop over parallel lists `T38` = words and
`T37` = text terms). Output: `J10` (attribute `K1` of current word) then `J152`
prints the term as one card, e.g. `V5   81   DREA`. `J16` ignores the
`K1` attribute because it only weighs numeric values, so sampling is unaffected.

**Probe first (`raven5a.ipl`):** `J152` on an alnum term prints `name 81 text`;
retrievable through a description-list attribute with `J10`.

**Result** (2 lines, 40 steps): ONCE UPON A MIDN DREA WHIL I POND WEAK AND WEAR
OVER MANY A QUAI AND CURI VOLU OF FORG LORE ONCE UPON A MIDN DREA WHIL I POND
WEAK AND WEAR OVER MANY A QUAI AND WEAR OVER MANY A.

**Bugs hit while building (mine):** loop labels must be `9-<digits>`, so `9-A`
silently did nothing; `alnum()` wrote only 2 chars of the name, so `V19`
overwrote `V1` (start word printed `LORE`).

---

## 2026-09-20 -- `raven4.ipl`: description-list bigram table with real counts (J10/J11/J16)

**Design change.** Each word `Tn` is a *describable list* (empty head cell);
its description list maps attribute = successor word -> value = integer count.
Training (routine `G2`): `J10` finds the count of (this) in prev's list; if
found `J125` adds 1 in place, else `J11` assigns a fresh copy (`J120`) of
constant one. Generation (routine `G1`) is just `J16` -- "FIND ATTRIBUTE
RANDOMLY", which the manual defines as a random pick among attributes with
positive numeric values, **weighted by those values** -- i.e. exactly a
count-weighted Markov step, no `J126/J129/J125/J200/J80` dance. Table print
(`--table`) walks a vocabulary list `T38` with `J150`. `mkdeck.py` now writes
`raven4.ipl`; the old repeat-encoded generator is `mkdeck3.py`/`raven3.ipl`.

**Result** (2 lines, 40 steps): table correct (e.g. `a -> {midnight:1,
quaint:1}`), generated text is legal bigrams:
*once upon a midnight dreary while i pondered weak and weary over many a
quaint and curious volume of forgotten lore once upon a midnight ...*

**Bugs found on the way (both matter beyond this project):**
1. **OCR error in `IPL-V-Subroutines.card`: `JB` should be `J8`** (lines 16 and
   36 = routines `J15` and `J16`). With `JB`, `J16` trapped forever
   (`TRAPPED ON 00001`). Fixed in place in
   `software/IPL-V/IPL-V-Subroutines.card` (2 lines changed; decision: no separate copy).
2. **Restore of working cells does not work**: `40W0 ... 30W0`, `J40/J30`,
   `J32` after `J52` all leave the *new* value in place (probes `traces/pr*.ipl`,
   `c_J3*.ipl`). Consequence: loaded routines that "preserve/restore" W0-W2
   (`J11`, `J12`, `J16`, ...) **clobber the caller's W0-W2** (probe `raven4b`:
   after `J11`, `W0..W2` = attribute, value, list). Workaround: `raven4` keeps
   its variables in `W4..W9`. Also implies each such call leaks pushdown cells.
   **Decision: not pursued for now; keep working around it (use W4..W9).** Root cause not found -- `PSHDN`/`POPUP` (`.sps` ~23270-23600) is the place to
   look; worth checking against Paul's old "pushdown" suspicion.

---

## 2026-09-19 (night) -- `raven3.ipl`: generator rolled into a loop; heavily commented

`mkdeck.py [nlines] [steps=40]` now emits a looped generator and ~45
comment cards. Unrolled `G1` x20 replaced by a counter loop: `W5` = fresh
copy (`J120`) of constant zero `N2` (copy so `J125` "add 1, leave" can't
mutate the constant); loop label `9-2`: push limit `N1`, push counter,
`J116` (test (0) < (1), so limit goes in first), `70 9-3` exits on `H5-`,
call `G1`, `11W5 J125 J8` (increment, pop leftover), link back to `9-2`.
Long explanations are **type-1 comment cards** (`1` in col 41, text in cols
7-40, wrapped by `mkdeck.py`); card-level comments are limited to 34 chars.
Region `N0 4` holds the two constants.

**Result:** 40 steps, clean halt, decoded: *once upon a quaint and curious
volume of forgotten lore once upon a midnight dreary while i pondered weak
and weary over many a quaint and curious volume of forgotten lore once upon a
quaint and weary over many a quaint*. All transitions legal; both branch
words (`a`, `and`) taken several ways.

---

## 2026-09-19 (evening) -- `raven3.ipl`: TRAINS the bigram table from text, then generates

`mkdeck.py [nlines] [steps]` tokenizes the first N lines of `raven.txt`
(lowercase, punctuation dropped), assigns symbols `T1..Tn` in first-seen order
(`raven3.vocab` = decode table), and writes `raven3.ipl`: embedded text list
`T39`, one *empty* successor list per word (named by the word's own symbol),
a training routine, table print, and a 20-step generator. Corpus: first two
lines = 21 tokens, 19 distinct. Run via `traces/runraven.sh` (Mod-3-4 deck).

**Training loop** (first IPL-V loop we've written; `W2`=cell, `W1`=previous
word, `W3`=this word, `W4`=first word): `11W2 J60` (next cell, `H5-` at end ->
`70 9-9`), `20W2`, `11W2 J80` (symbol in cell), then push prev, push this,
`J65` (insert (0) at end of list (1)), `W1 := this`, link back to label `9-1`.
Labels are `9-n` in the NAME column; loop-back is the LINK field of the last card.
After the loop `J8` pops the leftover cell and a wrap pair (last -> first) is
appended so no word is a dead end.

**Result -- table is exactly right** (`J151` of each list): once->upon,
upon->a, a->{midnight,quaint}, quaint->and, and->{weary,curious}, ...,
lore->once (wrap). Empty list heads (`Tn 0 ... link 0`) accepted by `J65`.

**Generated** (start `once`, 20 steps, decoded): *once upon a quaint and
curious volume of forgotten lore once upon a midnight dreary while i
pondered weak and weary*. Every step is a legal bigram; the two branch points
(`a`, `and`) were both taken. Deterministic per run (seed in deck).

**Not yet:** generator is still unrolled (20 `G1` calls); counts are
repeats, not `(succ,count)` pairs; corpus is 2 lines.

---

## 2026-09-19 (later) -- `raven2.ipl`: embedded text + dummy bigram table + generator WORKS

Run against the **Mod-3-4** interpreter (`traces/runraven.sh`, a gitignored
wrapper): the unpatched deck can't print numeric data terms (`J152` on a
`J126` count printed `??+ ??????????` -- the TNF Punch-Check bug), and
`raven` never calls `J66`, so Mod-3-4's `CF D6-4` regression is harmless here.

**Design (simplest thing that works).** Each word is a regional symbol
(`T1`..); the symbol *names its own successor list*, e.g. `T1 -> T2,T2,T3`.
Counts are multiplicities (`T2` twice = count 2), which makes uniform
random choice over list positions count-weighted. The embedded text is just
a data list `T9` (printed with `J151`). One generation step `G1` (12
unrolled calls, no loop yet), current word in `W0`:
```
11W0 11W0 J126   n = count of successor list of W0
J129             r = random in [0,n)      (manual: endpoint excluded)
J125             r+1                      (tally 1, leave)
J200             cell = (r+1)th cell of list
J80              symbol in that cell      (NOT J192 -- see below)
20W0 11W0 J152   W0 = next word; print it
```
**Output** (start `T1`): `T1 T2 T3 T2 T1 T2 T1 T3 T2 T3 T1 T3 T1 T3` -- every
transition is a legal edge of the table. Embedded text list printed OK.

**Gotchas learned:**
- `J192` (input SYMB of cell) crashes (`MAR Check: instruction at odd
  address 08459`) when given the internal cell name `J200` returns: it uses
  `J175`, which wants a *regional* symbol. Use `J80` (symbol in cell) instead.
- `J200` n is 1-based (n=0 gives the head cell); `J129` returns 0..n-1, so
  add 1 with `J125`.
- `J126` replaces the list with a data term count; `J129`'s randomness
  is seeded from the deck (`W10`), so every run gives the *same* sequence.
- `W0`..`W9` are system working storage: `20W0` sets, `11W0` reads.
- Full manual now extracted to `raven/manual.txt` (per page) and
  `raven/manual_flow.txt` (reflowed) via PyMuPDF in a scratch venv; both
  and the PDFs are gitignored (copyrighted).

Probe files: `raven2a.ipl` (`J126`), `raven2b.ipl` (`J129`/`J200` ranges).

---

## 2026-09-19 -- `raven1.ipl`: does `J180` (read a card at runtime) work? No -- silent no-op

Goal: the simplest possible program -- read one card, print it. Manual
(pp. 91-93, `Manual_R5-91-93.pdf`) documents `J180` "Read line" (card from
unit 1W18 into print line `X1`) and `J155` "Print line". `raven1.ipl`:
regions `A0`, `L0`, `X0`; print line `3 X1 01 80`; routine = `10X1`, `J180`,
`10X1`, `J155 0`. The card to be read (`raven1.data`, "THIS IS THE CARD TO
BE READ") is appended *after* Deck-2, so the loader doesn't consume it.

```
node tools/cli/run1620.mjs \
  software/IPL-V/IPL-V-Interpreter-Deck-1.card software/IPL-V/raven/raven1.ipl \
  software/IPL-V/IPL-V-Subroutines.card software/IPL-V/IPL-V-Interpreter-Deck-2.card \
  software/IPL-V/raven/raven1.data --timeout 30000
```

**Actual:** clean halt, 0 cards punched/printed, and **1 card still in the
hopper** -- `J180` did not read it. Trace: `traces/raven1_plain.log`.
Consistent with the routine-table grep: `J155`-`J162` and `J180`-`J189`
are not implemented in this interpreter (not in the `.sps` tables, not in
`IPL-V-Subroutines.card`); calling them is a silent no-op, not an error.

**Loading gotchas found on the way (each cost a failed run):**
- A regional symbol like `X1` needs its region declared first
  (`2 X0 10`) *before* the `3 X1 01 80` print-line card. Without it: `TYPE9
  +4 ILLEGAL LOADING ADDRESS`, then `A0 UNDEFINED REGIONAL SYMBOL` (the
  message names `A0`, not the real culprit).
- A card meant to be read by the *running* program must come after Deck-2
  in the deck order; put before `IPL-V-Subroutines.card`, the loader eats it
  and the load fails.
- Column numbers (1-indexed): TYPE col 41, NAME 43-44, PQ 49-50, SYMB 51-55,
  LINK right-justified to col 60 (region sizes are the exception: col 57).

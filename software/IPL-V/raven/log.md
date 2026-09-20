# `raven` Experiment Log

Same conventions as `../simple/log.md`: newest entries at the top, every run
logged, traces under `traces/` at the repo root.

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

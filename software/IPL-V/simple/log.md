# `simple` Experiment Log

Running record of experiments with the `simple*.ipl` test programs used to
validate individual IPL-V interpreter primitives in isolation via the CLI
harness (`tools/cli/run1620.mjs`). Each entry: the program run (full source,
since these are small), what was expected, what actually happened, and any
analysis/debugging steps taken. Separated by horizontal rules. Entries
through 2026-09-11 21:51 PDT (`simple3.ipl`, two-PRINT version) are in
oldest-first order; from the next entry on, newest entries go at the
**top**.

---

## 2026-09-12 (afternoon, later) — `simple12.ipl` (Jeff's): `J64` alone, inserting into an already-populated list

Built directly on the now-fixed `simple11.ipl`: locate `L3` (`J62`), then
call `J64` directly to insert a new symbol `L7` right after it, then
reload `L1` and print the whole list with `J151`.

```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
      LIST REGION                       2 L0            10
      ROUTINE HEADER. TYPE=5,Q=0.       5       00
      START A0 GET SYMB L1                A0    10L1
      WE WILL FIND L3                           10L3
      FIND IT                                     J62
      INSERT L7 AFTER L3                        10L7
                                                  J64
      PRINT OUT THE LIST NOW                    10L1
      PRINT THE LIST, QUIT.                       J151  0
      DATA HEADER. TYPE=5,Q=1.          5       01
      THE LIST L1.                        L1      0
                                                  L2
                                                  L3
                                                  L4    0
      START AT A0                       5         A0
```

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple12.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Actual:** clean halt, **no crash of any kind**. 5 cards punched:
`L1 0400000`, `L2`, `L3`, `L7`, `L4` -- `L7` correctly inserted right
after `L3`, exactly as intended. Trace saved at `traces/simple12_plain.log`.

**Analysis:** `J64` called directly, against an already-populated,
statically-built list, works correctly -- this rules out "any call to
`J64` crashes" as an explanation for the `F1.ipl`/`simple10.ipl` `RESBLK`
crash. That crash happens specifically when inserting into a list that
was just created *empty* via `J90`. Next isolation point for this
thread: does `J64` still work when the target list is a `J90`-created
empty list (skipping `J62`/`J66`'s search logic entirely and calling
`J64` directly on it), or does it fail only in that specific
just-created-empty-list case?

---

## 2026-09-12 (afternoon) — `simple11.ipl`: isolating `J62` (the "locate" half of `J66`), and a real logging lapse

Continuing the `F1.ipl`/`RESBLK` thread: since `IPL-V-Interpreter-Mod-3-4.sps`
shows `J66` is just a dispatcher that calls `J62` ("LOCATE (0) ON (1)",
line 1990) and, only if not found, `J64` (the actual list-insert), the
plan was to test each in isolation to find out which one is the real
`RESBLK`-crashing culprit.

**First version (mine):** took `simple10.ipl` and changed only the
`J66`->`J62` token (byte-identical everywhere else, diff-verified).
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple11.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```
**Actual:** clean halt, no crash. One card punched (`14723 0400000`, the
still-empty output list's header, since a pure locate doesn't add
anything). Full switches trace saved at `traces/simple11_monitor.log`.
**Analysis at the time:** J62 alone doesn't crash -> points at J64.

**Mistake (mine), corrected by Jeff:** immediately tried the same
`J66`->`J64` substitution for a would-be `simple12.ipl`, using the exact
same surrounding setup (`INPUT SYMBOL`/`INPUT LIST NAME`/`REVERSE` via
`J6`) that had worked for calling `J66` itself. Jeff caught this before it
ran: `JJ66`'s own code does extra setup (`BTM PSHDN,H0` / `CF D6-4` /
`TF H0-5,D6`) immediately before jumping into `J64` -- calling `J64`
directly the same way `J66` is called does not replicate what `J64`
actually expects as input. That file was deleted at Jeff's request; he
built his own `simple12.ipl` instead (in progress, not yet in this log).

**Then Jeff overwrote `simple11.ipl` with his own version** (correctly
so, per the plan -- he's driving this thread now), to test `J62` with a
much simpler setup: a statically-built `L1->L2->L3->L4` list (no `J90`/
`RESBLK` involved in building it), pushing `L1` then `L3` via two
`GET SYMB` calls, then calling bare `J62` (no `REVERSE`/`J6` step, no
`H0`/`W0` split), then `J152` to print/quit:
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
      LIST REGION                       2 L0            10
      ROUTINE HEADER. TYPE=5,Q=0.       5       00
      START A0 GET SYMB L1                A0    10L1
      WE WILL FIND L3                           10L3
      FIND IT                                   J62
      PRINT THE LIST, QUIT.                     J152  0
      DATA HEADER. TYPE=5,Q=1.          5       01
      THE LIST L1.                        L1      0
                                                  L2
                                                  L3
                                                  L4    0
      START AT A0                       5         A0
```
(One intermediate version had a typo -- `J152`'s column shifted slightly
-- fixed by Jeff; both versions gave the identical result below.)

**Actual (both versions):** clean halt, **no `MAR Check` crash**, but a
different failure: `OP CODE` error at address 19055 (where the bare
`J62` card sits), zero cards punched, before ever reaching `J152`.
```
Loaded 729 card(s) from 4 file(s).
    1 19055          OP CODE                     3
    1 19055          THE END                     3
```

**Analysis (wrong, in real time):** I guessed, in order, two incorrect
explanations before getting to the real one -- worth recording both as
what NOT to trust, not just the eventual right answer:

1. A stack-order/calling-convention mismatch (missing the `REVERSE`/`J6`
   setup). Wrong -- Jeff called this out directly.
2. A "clustered subroutine loading" theory: comparing this run's
   switches-trace subroutine table against the earlier working `J62` call
   (`traces/simple11_monitor.log`), the working run's table showed
   `4 J 060`, `4 J 062`, `4 J 064` all present, while this run's table
   showed only `4 J 010`, `4 J 064`, `4 J 170` -- no `J62` line. I
   concluded J62's code must not have been loaded at all, and that J60/
   J62/J64 load as a cluster triggered by referencing J60. Also wrong,
   and Jeff was right to reject it outright ("J62 can be called
   anytime") -- `IPL-V-Subroutines.card` is a fixed 80-line deck loaded
   in full, unconditionally, every single run (confirmed by reading the
   file directly); there is no selective/clustered loading mechanism.
   Whatever that subroutine-table trace section actually reflects, it
   is not "which primitive code is resident in memory."

**Actual cause (confirmed):** a plain column-alignment error on the
card itself, nothing to do with loading or calling convention. The `J62`
token was punched starting at column 48 (`FIND IT ... J62`) instead of
column 50. Column 48 is correct only when a 2-digit numeric op-code
prefix occupies columns 48-49 immediately before the symb value (as in
`10L1`/`10L3` on the two preceding lines, or `00J110` elsewhere in the
series) -- a bare `Jnn` primitive name with no such prefix belongs
starting at column 50 (matching every other successful bare-primitive
call in this whole series: `J66`, `J151`, `F1`, etc.). Shifting `J62`
two columns right (line 7's card now reads
`      FIND IT                                     J62`, `J62` at
column 50) fixed it completely:
```
Loaded 729 card(s) from 4 file(s).
             0419091

   0 19067           THE END                     4
```
Clean halt, no `OP CODE` error, one card punched (`0419091`), confirming
`J62` itself executed successfully once the card was punched correctly.
Trace saved at `traces/simple11_colfix.log`.

**Lesson:** don't theorize about interpreter-internal mechanisms (loader
behavior, calling conventions) from trace output alone when a much more
mundane explanation -- a column off by two -- fits the evidence just as
well and should be checked first. Both wrong theories above were
disproven by direct verification (reading `IPL-V-Subroutines.card`,
and simply re-checking the card's own columns) that should have been the
first move, not the second and third.

**Process note:** I stopped adding log entries after the `simple10.ipl`
entry below and only resumed here after Jeff pointed it out -- a real
gap, not a deliberate change in logging policy.

---

## 2026-09-11 23:30 PDT — `simple10.ipl` (new: minimal reproduction of the still-open `F1.ipl` crash)

Starts a new thread of experiments (rather than one-off `F1.ipl`
investigation) targeting the recursion/list-space bug first flagged by
Paul Kimpel, localized in an earlier session to the very first `J66`
(`COLSYM`, "add symbol to list if not already present") call in
`F1.ipl` — the first attempt to insert a symbol into a freshly-created,
still-empty output list, which coincides with the interpreter's very
first `RESBLK` ("reserve block") call in the whole run.

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple10.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program:** identical `E1` (executive) + `F1` (worker) routine bodies to
`notes/F1.ipl`, and all six of its region declarations (`A0`-`F0`, `K0`)
kept even though only `K0` is used — see the load-time gotcha below.
Only change: the input list `K1` is shrunk from 6 elements
(`B1,C1,B1,A1,A1,B1`) to 1 (`K2`, self-referencing the already-declared
`K0` region, the same trick used in `simple8`/`simple9` — no need for a
separate content region).
```
      TYPE=9, FIRST CARD.               9
      MINIMAL REPRO OF F1 FAILURE.      1
      THE A-REGION=10 CELLS, A0-A9.     2 A0            10
      THE B-REGION=10 CELLS, B0-B9.     2 B0            10
      THE C-REGION=10 CELLS, C0-C9.     2 C0            10
      THE E-REGION=10 CELLS, E0-E9.     2 E0            10
      THE F-REGION=10 CELLS, F0-F9.     2 F0            10
      THE K-REGION=10 CELLS, K0-K9.     2 K0            10
      ROUTINE HEADER. TYPE=5,Q=0.       5       00
      Q=3 SAYS TRACE THIS ROUTINE.        E1    13K1
      EXECUTE F1 AND                              F1
      PRINT THE OUTPUT LIST.                      J151  0
      ROUTINE HEADER, TYPE=5,Q=0.       5       00
      CREATE AN EMPTY OUTPUT LIST.        F1    04J90
      PRESERVE W0.                              40W0
      W0 HOLDS NAME OF OUTPUT LIST.             20W0
      LOCATE NEXT CELL OF INPUT LIST.     9-1     J60
      GO TO 9-2 IF NO NEXT CELL.                709-2
      INPUT THE SYMBOL IN THE CELL.             12H0
      INPUT THE NAME OF THE OUTPUT LIST.        11W0
      REVERSE THEIR POSITION IN H0, AND           J6
      ADD THE SYMBOL TO THE OUTPUT LIST           J66   9-1
      PUT THE NAME OF THE OUTPUT LIST     9-2   51W0
      IN H0 AND RESTORE W0 BEFORE               30W0    0
      DATA HEADER. TYPE=5,Q=1.          5       01
      THE LIST K1.                        K1      0
                                                  K2    0
      START CARD. EXECUTE E1.           5         E1
```

**Load-time gotcha found along the way:** a first attempt dropped the
unused `A0`/`B0`/`C0`/`E0`/`F0` region declarations entirely (keeping
only `K0`, the one actually referenced). That load produced
`UNDEFINED REGIONAL SYMBOL` errors on labels that have nothing obviously
to do with those regions (`TYPE9 +5`, `E1 +1`, `E1 +4`, `K1 +2`,
`J170 +10`) — and, notably, the check-stop still happened at the same
address (`70603`), so the crash itself wasn't caused by this. Restoring
all six original region declarations (unused ones included) made the
load-time errors disappear completely, with no other change. Not
explained yet — logged as a separate open question: something about the
assembler's symbol-table layout appears sized/offset relative to the
*number* of `DEFINE REGIONS`-type cards in the deck, not just which
regions are actually referenced. Worth remembering before trimming region
declarations in future minimal repros.

**Expected:** the same `MAR Check: fetch() invalid memory
address=70603` check-stop as `F1.ipl` itself, at the same `J66` call,
regardless of the input list's length (since the crash was already
localized to the *first* `J66` call specifically).

**Actual:** Confirmed exact match.
- Plain run: identical check-stop, `MAR Check: fetch() invalid memory
  address=70603`, zero cards punched (crashes before ever reaching
  `J151`).
- `--switches 1,2,3,4` monitor trace confirms it dies at the identical
  point in the routine: the trace's last successful step is
  `J66 19631 ... K2 ... 00000` (the `ADD THE SYMBOL TO THE OUTPUT LIST`
  call), immediately followed by the check-stop — same statement, same
  primitive, same address, as in the original 6-element-list run.

**Analysis:** Success — this is now a clean, minimal, committed starting
point for a dedicated experiment thread on this bug (rather than reusing
`notes/F1.ipl` directly, which is untracked, was written by Paul rather
than as part of this series, and carries extra scaffolding not needed
once the crash is already localized to a single primitive call). Next
experiments in this thread can build on `simple10.ipl` directly — e.g.
varying what's on the input list, trying an already-non-empty output list
(skip `J90`, use a statically-declared one-element list instead, as
`simple8.ipl` showed works), or adding tracing/memory inspection focused
specifically on the `TF` instruction's operands (`NMBR`/`LADR`) right
before the crash, per the still-open question flagged in
`20260911b_seshsum.md`.

---

## 2026-09-11 23:05 PDT — `simple9.ipl` (new: build a list via `GET SYMB` pushes, not `DATA HEADER` cells)

Follow-up to `simple8.ipl`: that test built its list the "static" way, via
`DATA HEADER`/list-cell cards declared at load time. This test instead
builds a list purely at runtime, by calling `GET SYMB` (op `10`) five
times in a row with no `PRINT`/`J152` in between, then a single
`PRINT THE LIST, QUIT.` (`J151`) at the end.

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple9.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
      LIST REGION                       2 L0            10
      ROUTINE HEADER. TYPE=5,Q=0.       5       00
      START A0 GET SYMB L1                A0    10L1
                                                10L2
                                                10L3
                                                10L4
                                                10H0
      PRINT THE LIST, QUIT.                       J151  0
      DATA HEADER. TYPE=5,Q=1.          5       01
      START AT A0                       5         A0
```

**Expected (predicted before running):** based on `simple7.ipl`'s
multi-`GET SYMB` ADD setup (push operand2, push operand1, push result-name
again, before `J110` pops via the `GET3` convention), `GET SYMB` was
suspected to be a genuine **push onto the H0 pushdown list**, not a
same-register overwrite as it appeared to be in the single-push
`simple1`-`simple6.ipl` tests (where only one item was ever on the stack
at a time, so push-vs-overwrite was indistinguishable). If so, pushing
`L1`, `L2`, `L3`, `L4`, then `H0` should build a 5-element list under H0
in LIFO order, and `J151` should print all five elements — not just the
last one pushed.

**Actual:** Clean halt, no errors. Card punch (5 cards): a header card
showing `H` / `H` (two tokens, at the same two column offsets `simple8`'s
`L1 0400000` header card used for name/pointer-encoding), followed by
`L4`, `L3`, `L2`, `L1` — in that exact order. Typewriter: `THE END    6`.

**Analysis:** Confirms the hypothesis. The print order (`H0`, `L4`, `L3`,
`L2`, `L1`) is precisely the *reverse* of the push order in the source
(`L1, L2, L3, L4, H0`) — i.e. last-pushed-prints-first, the signature of
a LIFO pushdown list built by repeated `GET SYMB` calls with `H0` as the
list head/top-of-stack pointer. `J151` walks that same pushdown chain
head-to-tail, exactly as it walked the statically-declared `L1->L2->L3
->L4` chain in `simple8.ipl`. Pushing the symbol `H0` itself (the pushdown
list's own head register) as the final "content" item worked without
error and round-tripped cleanly — it's a valid regional reference
(`H`-region, cell `0`) like any other, even though H-cells are normally
used internally by the interpreter rather than as ordinary data. Key
transferable lesson: **`GET SYMB` is IPL-V's push-onto-H0-list primitive,
not a plain assignment** — every `simple*.ipl` test so far that only ever
pushed one item at a time looked like an overwrite purely because a
1-element stack and an overwritten register are indistinguishable from
the outside.

**Addendum (same session, follow-up question):** Jeff pushed back on
over-generalizing this result: "generally speaking, pushing to lists
works... unless the interpreter has specialized code for H0." Correct
concern — checked directly with a full untruncated `--trace` of this same
run (no delay, ~93,900 lines) and grepped for both list-space-allocator
entry points used elsewhere (`FNDBLK` at `08002`, `RESBLK` at `08248`,
per the `F1.ipl` investigation in `20260911b_seshsum.md`):

- `FNDBLK`: called exactly 32 times, all clustered early (last occurrence
  at trace line 14391 of 93873) — matching the same "32 harmless bootstrap
  calls" identified during interpreter H2-free-list initialization in the
  `F1.ipl` trace, i.e. **not** triggered by this program's own logic.
- `RESBLK`: called **zero** times.

None of this program's 5 `GET SYMB` pushes, nor its `J151` print, touch
either allocator. **Conclusion: `simple9.ipl` does not demonstrate that
dynamic list growth works in general — it demonstrates that H0's
pushdown-list push is a separate mechanism that bypasses the block
allocator entirely**, almost certainly fixed/pre-reserved H-register
storage rather than an ordinary dynamically-growable list. This is
consistent with H being one of the reserved/special region letters. It
says nothing about whether `J66`/`COLSYM` (the *actual* dynamic-list-growth
primitive, and the one still crashing in `F1.ipl`) works on an ordinary
list — that remains completely untested, and a minimal isolated test of
it would just be a smaller reproduction of the still-open `F1.ipl` bug,
not a new data point.

---

## 2026-09-11 22:34 PDT — `simple8.ipl` (new: build and print a list)

Pivoted here from an in-progress `F1.ipl` crash investigation (see
separate discussion — not logged in this file, whose scope is the
`simple*.ipl` series) to try something more basic: construct a small
IPL-V list and print it with `J151`, the list-print primitive `F1.ipl`
itself uses.

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple8.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program (final, working version):**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
      LIST REGION                       2 L0            10
      ROUTINE HEADER. TYPE=5,Q=0.       5       00
      START A0 GET SYMB L1                A0    10L1
      PRINT THE LIST, QUIT.                       J151  0
      DATA HEADER. TYPE=5,Q=1.          5       01
      THE LIST L1.                        L1      0
                                                  L2
                                                  L3
                                                  L4    0
      START AT A0                       5         A0
```

**First attempt (failed) and the fix:** Built column-exact from
`notes/F1.ipl`'s own known-working region/list-cell templates (verified
token-for-token identical field positions), but used invented symbol
names `X1`/`Y1`/`Z1` for the three list cells' content. That produced,
during loading: `L1 +1  UNDEFINED REGIONAL SYMBOL`, `L1 +2  UNDEFINED
REGIONAL SYMBOL`, `L1 +3  UNDEFINED REGIONAL SYMBOL` (region size wasn't
the issue — tried both size 5 and size 10 for `L0`, same error either
way; also ruled out the region *name* `L0`/`D0` as the problem via a
substitution test). **Jeff's correction**: a list cell's content symbol
in IPL-V isn't arbitrary label text — it's itself a region-letter +
digit reference (exactly how `F1.ipl`'s own list content `B1`/`C1`/`A1`
works: those are live references into `F1.ipl`'s already-declared `B0`/
`C0`/`A0` regions, not just printable tags). `X1`/`Y1`/`Z1` referenced
regions `X0`/`Y0`/`Z0` that were never declared. Fix: reuse the
already-declared `L0` region for the content atoms too (`L2`, `L3`,
`L4`), self-referential with the list's own continuation-cell addresses
but syntactically fine.

**Expected (after the fix):** A clean load, no "undefined regional
symbol" errors, and `J151` printing the list's contents to the card
punch.

**Actual:** Card punch (4 cards punched): `L1 0400000`, `L2`, `L3`, `L4`.
Typewriter: `THE END                     2`. Clean halt, no errors, no
crash, no timeout.

**Analysis:** Success — first working list-construction-and-print test
in the `simple*.ipl` series. The list `L1 -> L2 -> L3 -> L4` was built via
plain data-header cards (no `J90`/list-processing primitives involved
yet, just the assembler's own static list-literal syntax) and printed
correctly by `J151`, one punched card per element (header included). Key
transferable lesson for future list-based `simple*.ipl` tests: **any
symbol used as a list cell's content must itself be a valid, pre-declared
regional reference** (either reusing the list's own region, as done
here, or a separate region declared for that purpose, as `F1.ipl` does
with its `A`/`B`/`C` regions) — it is not free-form text.

## 2026-09-11 22:18 PDT — `simple7.ipl` (new: isolated `J110` ADD, right-justified)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple7.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program:** Same 3-operand `J110` calling convention validated last
session (`hold_8.ipl`, formerly `simple8.ipl`: push operand 2, push
operand 1, push the destination name again, call `J110`), renamed
`A3`/`A4` → `A1`/`A2`, with the `CONSTANT` values now right-justified per
the `simple6.ipl` fix above:
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            6
                                        5       00
      GET SYMB A2 (OPERAND 2)             A0    10A2
      GET SYMB A1 (OPERAND 1)                   10A1
      GET SYMB A1 AGAIN (RESULT NAME)           10A1
      ADD THEM: A1 = A1 + A2                    00J110
      INPUT A1 = RESULT (FRESH)                 10A1
      PRINT RESULT, QUIT.                         J152  0
                                        1
                                        5       01
      CONSTANT 3                          A1    01          3
      CONSTANT 4                          A2    01          4
      START AT A0                       5         A0
```

**Expected:** `A1`(=3) + `A2`(=4) = 7, punched as plain `7` (not
`70000`), given the LINK-field fix now in place.

**Actual:**
- Card punch (1 card punched): `A1 01 7`.
- Typewriter: `THE END                     6`.
- Completed cleanly, no crash, no timeout.

**Analysis:** Correct, and cleanly so this time — no scaling artifact to
explain away. `J110`'s 3-operand `GET3` convention (destination pushed
twice + one real operand) plus the right-justified constant format
together produce exactly the right answer with a single punched card
(only the fresh post-add `INPUT A1` print fires, since — per the
STOP-marker finding two sessions back — there's only one terminating
`PRINT RESULT, QUIT.  0` in this program, unlike `simple4`'s two-print
version). First real "does the interpreter compute the right sum"
confirmation with both known formatting bugs (STOP-marker
misunderstanding, LINK left-justification) already accounted for.

## 2026-09-11 22:16 PDT — Fixed and re-ran `simple1.ipl`-`simple5.ipl` with right-justified constants

Follow-up to the `simple6.ipl` confirmation above: applied the same fix
(right-justify each `CONSTANT` card's value digit to column 60, the last
column of the 5-column LINK field) to `simple1.ipl` through `simple5.ipl`
in place, then re-ran all five.

**Command (per file):**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/<file>.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Results (all clean halts, no crashes/timeouts):**

| File | Punch output (before fix) | Punch output (after fix) |
|---|---|---|
| `simple1.ipl` | `A1 01 30000` | `A1 01 3` |
| `simple2.ipl` | `A1 01 70000`, `A2 01 50000` | `A1 01 7`, `A2 01 5` |
| `simple3.ipl` | `A1 01 70000`, `A2 01 50000` | `A1 01 7`, `A2 01 5` |
| `simple4.ipl` | `A1 01 70000→70001`, `A2 01 50000→50001` | `A1 01 7→8`, `A2 01 5→6` |
| `simple5.ipl` | `A1 01 70000→70001`, `A2 01 50000→50001` | `A1 01 7→8`, `A2 01 5→6` |

Every value now reads as the plain, intended integer, and both `J125`
increments (`simple4`/`simple5`) are now correctly `+1` in the ordinary
sense (`7→8`, `5→6`) rather than the field-mismatched `70000→70001`
pattern. `simple4.ipl` and `simple5.ipl` are now content-identical to the
already-fixed `simple6.ipl` (their only prior difference — a 2-column
shift in the constant's position — no longer matters now that both sit
correctly right-justified at column 60).

**Analysis:** No new findings beyond confirming the `simple6.ipl` fix
generalizes cleanly across every existing test in the family. This
retroactively invalidates the "x10000 encoding" framing used in every
`simple1`-`simple5` log entry above (all logged before this fix) — those
entries are left as-is per instruction (no flipping old entries), but
should be read with this correction in mind: there was no encoding, just
a left-justification bug in the source cards. The `hold_2.ipl`-
`hold_8.ipl` files (set aside from the prior session, not part of the
active `simple*.ipl` series) were **not** fixed or re-run here.

## 2026-09-11 22:15 PDT — `simple6.ipl` — CONFIRMED: the "x10000" field was our own left-justification bug

**Jeff's hypothesis, stated after `simple5.ipl`:** "I think we're putting
in the numbers in the wrong format." Specifically: the `CONSTANT` cards'
value digit has been left-justified in the LINK field, when it should be
right-justified.

**Supporting fact found before testing:** `IPL-V-Interpreter-Mod-3-4.sps`
line 1562 declares `LINK  DS  5,` — LINK genuinely is a fixed 5-digit
storage field, matching the 5-digit values (`70000`, `50000`, etc.) seen
in every punch dump so far.

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple6.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program:** Identical to `simple4.ipl`/`simple5.ipl` except the
`CONSTANT` cards' value digit moved 4 columns right, from column 56 to
column 60 (the last column of the presumed 56-60 LINK field):
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            3
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152
      GET SYMB A2                               10A2
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01          7
      CONSTANT 5                          A2    01          5
      START AT A0                       5         A0
```

**Expected:** If the hypothesis is right, the punch dump should show
plain `7`/`5` (not `70000`/`50000`), and `J125` should correctly bump them
to `8`/`6` (not `70001`/`50001`).

**Actual:**
- Card punch (4 cards punched): `A1 01 7`, `A1 01 8`, `A2 01 5`,
  `A2 01 6`.
- Typewriter: `THE END                     8`.
- Completed cleanly, no crash, no timeout.

**Analysis — this resolves the single biggest open question from the
2026-09-10 session:**
- **Confirmed correct.** Right-justifying the constant's digit within the
  5-column LINK field produces exactly the right values: `A1` goes
  7→8, `A2` goes 5→6. `J125` was never broken and was never operating on
  "the wrong field" — it was always correctly incrementing the LINK
  field's units digit; **our own hand-written `.ipl` cards had been
  putting the digit in the field's leftmost (ten-thousands) column
  instead of its rightmost (units) column**, with the blank trailing
  columns reading as zero. `70000`→`70001` was IPL-V doing exactly the
  right thing to a badly-formatted operand.
- **This also retroactively reframes the prior session's `simple8.ipl`
  result** (traced `J110` add: `30000`+`40000`→`70000`, at the time
  reported as "confirmed correct 3+4=7 in a value x10000 encoding").
  There is no "x10000 encoding" — that was the same left-justification
  artifact. The arithmetic was genuinely correct (30000+40000=70000 is
  simple correct integer addition), just performed on operands we had
  accidentally scaled up by 10000x through bad card formatting, not on
  the intended small operands 3 and 4.
- **Practical rule for all `simple*.ipl` cards going forward:** a data
  term's numeric value must be right-justified within its (apparently
  5-column) field, e.g. a single-digit value's digit belongs in the
  field's *last* column, not its first. `simple1.ipl` through `simple5.ipl`
  (and presumably `hold_2.ipl`-`hold_8.ipl` from the prior session) all
  used the wrong (left-justified) placement.

## 2026-09-11 22:13 PDT — `simple5.ipl` (Jeff's hypothesis: `CONSTANT` value column position)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple5.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 30000
```

**Program:** Identical to `simple4.ipl` except the `CONSTANT` cards' value
column shifted 2 columns left:
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            3
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152
      GET SYMB A2                               10A2
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01    7
      CONSTANT 5                          A2    01    5
      START AT A0                       5         A0
```
(vs. `simple4.ipl`'s `CONSTANT 7                          A1    01      7`
— the trailing `7`/`5` moved 2 columns earlier.)

**Expected:** Jeff's hypothesis (not yet stated to me in detail — flagged
here for follow-up) was that shifting the `CONSTANT` value's column
position might interact with the `J125` field-mismatch mystery
(`simple4.ipl` showed `J125` bumping `70000`→`70001` instead of the
expected `70000`→`80000`).

**Actual:** Byte-for-byte identical to `simple4.ipl`'s run: card punch
`A1 01 70000`, `A1 01 70001`, `A2 01 50000`, `A2 01 50001`; typewriter
`THE END 8`; clean halt.

**Analysis:** The 2-column shift made no observable difference — same
punch output, same `J125` behavior (still incrementing the trailing digit
rather than the leading "value" field). Whatever encodes a `CONSTANT`
card's value, it isn't sensitive to this particular column shift (at
least not in a way this test could detect). Follow-up needed: get the
actual hypothesis from Jeff to determine whether this genuinely tests it
or whether a different column/field needs to move instead.

## 2026-09-11 22:05 PDT — Harness change: disabled real-time throttling

Not a `simple*.ipl` experiment — a change to `tools/cli/run1620.mjs`
prompted directly by the `simple4.ipl` timing investigation below (the
~15.6-15.9s baseline wall-clock time that made `--timeout 15000` flaky).

**Change:** `run1620.mjs` now overrides `processor.envir.throttle` to a
no-op (`() => Promise.resolve()`) by default right after constructing the
`Processor`, skipping the real-1620-speed pacing `envir.throttle()`
normally provides. Added a `--real-time` flag to opt back into the
original throttled timing, for the rare case of debugging something
timing-sensitive (e.g. a device interlock). Also updated
`tools/cli/README.md`'s "Known limitations" section to describe this.

**Why:** There's no real hardware for a headless CLI run to stay in sync
with, so the throttling was pure overhead — and it was large enough
(~15.6-15.9s just to load the ~700+ card interpreter deck, regardless of
program size) to make a 15s timeout falsely look like a hang.

**Verified:** Re-ran `simple1.ipl`, `simple2.ipl`, `simple3.ipl`, and
`simple4.ipl` after the change — all four produced byte-identical
typewriter/punch output to their previously-logged runs (same `THE END`
numbers, same punch card contents), confirming the change only affects
speed, not behavior. Wall-clock time dropped from ~15.6-15.9s to ~3.6-3.7s
for both `simple1.ipl` and `simple4.ipl`.

---

## 2026-09-11 21:57 PDT — `simple4.ipl` (new: adds `J125` increments)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple4.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 15000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            3
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152
      GET SYMB A2                               10A2
      PRINT RESULT, QUIT.                         J152
      INCREMENT IT                                J125
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01      7
      CONSTANT 5                          A2    01      5
      START AT A0                       5         A0
```

**Expected:** Push `A1`(=7), print, increment (`J125`), print again —
expect the second print to show 8 in whatever field carries the value;
then the same for `A2`(=5) expecting 6. Also expect a clean halt at the
final, STOP-marked `PRINT RESULT, QUIT.  0`.

**Actual (corrected — see below):**
- Card punch (4 cards punched): `A1 01 70000`, `A1 01 70001`, `A2 01 50000`,
  `A2 01 50001`.
- Typewriter printed `THE END                     8`.
- First pass at `--timeout 15000` reported `--- run1620: timeout ---`
  ("No halt within 15000ms"). **This was a false alarm, corrected by a
  follow-up check** (see Analysis): re-run at `--timeout 60000` halted
  cleanly (`--- run1620: halted ---`) after ~15.6-15.9s wall-clock —
  right at the edge of the 15000ms cap used originally. A same-parameters
  re-run of `simple1.ipl` (previously logged as completing fine) also
  measured ~15.6s wall-clock at `--timeout 60000`, confirming this
  ~15-16s figure is **not specific to `simple4` or to `J125`** — it's the
  fixed cost of the interpreter/assembler loading its own ~720-730 cards
  (dominated by `envir.throttle()`'s real-time-paced instruction
  execution during Deck-1/Subroutines/Deck-2 loading), roughly constant
  regardless of how small the user's own program is. `--timeout 15000`
  is simply too tight a margin for this harness/deck combination and
  produces flaky pass/fail near that boundary.

**Analysis:**
- `J125` incremented the **last digit** of the punched field (`70000` →
  `70001`, `50000` → `50001`), not the leading "value" digits (which would
  have been `80000`/`60000` for a real +1 to the mantissa). This matches
  the still-unresolved finding from the prior session: `J125` operates on
  a different field (the LINK-area low digits per the IPL-V manual, p.44)
  than the "value x10000" field that `simple2`/`simple3` showed being
  read/printed directly. Not yet reconciled — still the open question
  flagged in the 2026-09-11 session summary.
- The apparent "hang after THE END" was **not a real bug**: a
  `--trace --trace-after 729` re-run showed the processor correctly
  reaching its final `H` (halt) instruction at address `03082`, auto-
  restarting once per the harness's normal multi-phase-boot handling, and
  landing on the same halt address a second time with no further
  progress — exactly the documented "halted" condition, not a runaway
  loop. The only problem was the 15s timeout being shorter than this
  harness's actual ~15.6-15.9s baseline completion time.
- **Going forward: use a longer `--timeout` (the script's own 30000ms
  default, or higher) for anything beyond the most trivial `simple*`
  case**, rather than the 15000ms used in earlier log entries — that
  margin is too thin for this interpreter/deck combination and risks
  misreading a slow-but-correct run as a hang.

---

## 2026-09-11 21:42 PDT — `simple1.ipl` (formerly `simple.ipl`)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple1.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 15000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 3                          A1    01      3
      START AT A0                       5         A0
```

**Expected:** Per `software/IPL-V/README.txt`'s own longstanding
characterization, this is "a minimal IPL-V program that runs, but
effectively does nothing" — it pushes the data-term `A1` (declared
`CONSTANT 3`) onto the stack and immediately calls `PRINT RESULT, QUIT.`
(`J152`) without ever calling an arithmetic primitive, so no computed
result is expected on the typewriter. Not previously confirmed whether it
even completes cleanly under the harness, or what actually lands on the
card punch.

**Actual:**
- Typewriter: `THE END                     2` (no "3" anywhere).
- Card punch (1 card punched): `A1       01        30000`.
- Completed cleanly, no crash, no timeout, no restart.

**Analysis:**
- Confirms the finding from the 2026-09-10 session: `J152`'s actual
  result output goes to the **card punch** (via SYMOUT), not the
  typewriter. The punch line shows `A1 01 30000` — the data term's name
  (`A1`), P/Q digit (`01`), and its value-bearing field showing `30000`,
  i.e. the "value x10000" encoding established previously (3 -> 30000).
  This is `A1` still holding its original declared constant (3), exactly
  as expected for a program that does no arithmetic.
- The typewriter's "THE END `<n>`" trailing number (`2` here) is
  reconfirmed as an unrelated, generic completion code — not a computed
  result — consistent with prior sessions' finding that this number
  doesn't reliably track anything program-specific.
- No new bugs found; this run's purpose was to re-baseline `simple1.ipl`
  under the reorganized directory layout and confirm the harness +
  Mod-3-4 decks still load and run it identically to before the move.

---

## 2026-09-11 21:47 PDT — `simple2.ipl` (new; same as `simple1.ipl` but `3`→`7`)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple2.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 15000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01      7
      START AT A0                       5         A0
```

**Expected:** Identical to `simple1.ipl` except `A1`'s declared constant is
`7` instead of `3`. Purpose: a sanity check that the card-punch output
we've been reading actually reflects the declared value in the source,
rather than being some fixed/incidental `30000` we happened to see once
and mistook for signal.

**Actual:**
- Card punch (1 card punched): `A1       01        70000`.
- Typewriter: `THE END                     2` (same trailing number as
  `simple1.ipl` — unchanged, as expected, since it's an unrelated
  completion code).
- Completed cleanly, no crash, no timeout, no restart.

**Analysis:**
- The punch output tracked the source change exactly: `3`→`30000` in
  `simple1.ipl`, `7`→`70000` here. This rules out the punch line being a
  hardcoded/incidental value and confirms the "value x10000" encoding
  read there really is driven by the program's own declared constant.
- No new bugs found; this was a confirmation run, not a primitive test.

---

## 2026-09-11 21:50 PDT — `simple3.ipl` (new)

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple3.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 15000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            2
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01      7
      START AT A0                       5         A0
```

Note: this is identical to the original (pre-edit) `simple2.ipl` — a
single `GET SYMB A1` / `PRINT RESULT, QUIT.` with `A1` = 7. In the
meantime `simple2.ipl` was independently edited (by Jeff) to add a second
data term `A2` = 5 and a second `GET SYMB`/`PRINT` block, so the two files
have since diverged.

**Expected:** Same behavior as the earlier `simple2.ipl` run above — punch
shows `A1 01 70000`, typewriter shows the generic "THE END 2".

**Actual:**
- Card punch (1 card punched): `A1       01        70000`.
- Typewriter: `THE END                     2`.
- Completed cleanly, no crash, no timeout, no restart.

**Analysis:** Matches expectations exactly — same program, same result.
No new bugs found.

---

## 2026-09-11 21:51 PDT — `simple3.ipl` (edited: two data terms, two PRINTs)

Jeff edited the file in place between runs; re-checked after the edit.

**Command:**
```
node tools/cli/run1620.mjs \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card \
  software/IPL-V/simple/simple3.ipl \
  software/IPL-V/IPL-V-Subroutines.card \
  software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card \
  --timeout 15000
```

**Program:**
```
      SIMPLE TEST FOR IPL-V             9
      DEFINE REGIONS                    2 A0            3
                                        5       0
      START A0 GET SYMB A1                A0    10A1
      PRINT RESULT, QUIT.                         J152
      GET SYMB A2                               10A2
      PRINT RESULT, QUIT.                         J152  0
                                        5       01
      CONSTANT 7                          A1    01      7
      CONSTANT 5                          A2    01      5
      START AT A0                       5         A0
```

Note: `A0`'s first `PRINT RESULT, QUIT.` (line 5) is missing the trailing
`0` that the second one (line 7) has. Per Jeff: in IPL that trailing `0`
is not an operand at all — it's a **STOP marker**, denoting end-of-list
for the routine. So line 5's `J152` (no `0`) means routine `A0`'s
instruction list continues to the next card; line 7's `J152  0` (with
`0`) marks the actual end of `A0`'s list.

**Expected:** Unclear going in — this is a new two-step program (push
`A1`=7 and print, then push `A2`=5 and print) rather than a repeat of a
known-working case. Open question: does the first "PRINT RESULT, QUIT."
actually halt execution (as `J152`'s name implies), or does execution
continue to the second `GET SYMB`/`PRINT` block regardless?

**Actual:**
- Card punch (2 cards punched): `A1 01 70000`, then `A2 01 50000` — both
  data terms punched, in order.
- Typewriter: `THE END                     4` (single completion message,
  after both punches).
- Completed cleanly, no crash, no timeout, no restart. Card count: 726
  (3 more than `simple1`/`simple2`/`simple3`'s earlier 723, consistent
  with the extra `GET SYMB`/`PRINT` cards).

**Analysis:**
- Both `PRINT RESULT, QUIT.` calls executed and both data terms were
  punched. This is now explained, not surprising: the trailing `0` isn't
  an operand to `J152` — it's IPL's own **STOP/end-of-list marker** for
  the routine (Jeff's correction). Line 5's bare `J152` just means `A0`'s
  instruction list isn't done yet, so execution correctly fell through to
  `GET SYMB A2` and the second, properly-terminated `J152  0`. So this
  ran exactly as it should, given the card format — not a quirk of
  `J152`'s semantics at all, just routine-list continuation working as
  designed.
- The "THE END `<n>`" trailing number (`4` here, vs `2` for the
  single-PRINT programs) changed between runs for the first time —
  another data point suggesting this number is some kind of
  operation/step count rather than a fixed constant, though still not
  confirmed to be the actual computed result (it doesn't match either 7,
  5, or 12).

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

# IPL-V trace control: the console (program) switches

Source: `software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4.sps`, routines `TRACE` / `TRTRP`
(SPS lines 23820-24040, object addresses 02790-02932). Read from the listing only; **not yet
confirmed by running** (see "To verify").

## What the code does

`TRACE` decides whether to emit an IPL-V trace line for the instruction about to execute.
The decision is recorded in a one-digit indicator, `TCIND` (address 02827, defined as
`DS ,TRTRP-1`, i.e. the byte just before `TRTRP`).

1. `TRACE` does `BTM TRTRP,0,10,`, which clears `TCIND` to 0 (see the comment at line 23850).
   It then does `BNF PRIMSW,TCIND`: unflagged means no trace, continue at `PRIMSW`; flagged
   means `B TRACE1`, which builds the trace line.
2. `TRTRP` first tests `H6` (`BNF *+14,H6`). If `H6` is flagged it returns at once, so **nothing
   is traced**.
3. `BC1` (switch 1 ON) jumps to the switch-1 logic (02882). `BC2` (switch 2 ON, 1 off) jumps
   straight to `SETIT`. Neither on: return, no trace.
4. `SETIT` does `TDM TCIND,1,11` (flagged 1 into `TCIND`) and returns: "trace this one".
5. Switch-1 logic (02882):
   - switch 2 off: `BD SETIT,H1-11` traces only if the digit at `H1-11` is nonzero. This is
     read as the Q digit of the current instruction (`H1` is the current instruction cell).
   - switch 2 also on: `BNF *+36,TRIND` returns with no trace if `TRIND` is unflagged; if
     flagged, `BD SETIT,TRIND` traces when its digit is nonzero; otherwise fall through to
     the `H1-11` test above.

## Resulting behavior

| Program switches ON | Effect |
|---|---|
| none | no trace |
| 2 only | trace **every** instruction |
| 1 only | trace only instructions whose Q digit (`H1-11`) is nonzero |
| 1 and 2 | trace if `TRIND` is flagged and nonzero, or Q digit nonzero; else no trace |

A flagged `H6` suppresses tracing in every case. Trace output goes to the card punch (the
typewriter only for the "typed trace" path at `SHTYP`, line 24260, which also tests `H6`).

## Open questions

- **`H6`**: defined at line 20810; also gates entry at `TTEST` (line 21570). Its IPL-V meaning
  is not established; guess is a trace-suppress flag.
- **`TRIND`** (line 25280): set to a flagged 7, flagged 1, or flagged 0 by the Q=3 handling
  (lines 22340-22430, depending on a counter at `TEMP3`). Guess: state for "trace this routine
  and what it calls". Not worked out.
- **`H1-11`** as the Q digit: inferred from the earlier observation that switch 1 needs the Q
  digit set; the offset was not checked against the cell layout.
- Switches 3 and 4 (J-routine linkage info; source/object dump) are handled elsewhere and are
  not covered here.

## To verify

Run `tools/cli/run1620.mjs --switches 1`, `2` and `1,2` on `software/IPL-V/Ackermann.ipl` and
compare the punched trace against the table above.

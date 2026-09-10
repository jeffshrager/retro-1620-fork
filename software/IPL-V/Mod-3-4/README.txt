IBM-1620 IPL-V Interpreter -- Modification Letters 3 & 4 applied.

Contributed by Paul Kimpel (author of the retro-1620 emulator), from work
done studying the behavior of the Ackermann function test program
(../Ackermann.ipl) in this IPL-V port.

Background
----------

The interpreter in ../IPL-V-Interpreter.sps uses the TNF instruction
(Transfer Numeric Fill, op code 72) to translate BCD digit fields into
1620 two-digit alphanumeric codes (interleaving each source digit with a 7,
or a 5 if the source's high-order digit is flagged, per the old punched-
card sign convention). The 1620 Model 2 requires that the alphanumeric
field written by a TNF be at an odd address. Many of the TNF instructions
in the transcribed interpreter use an even address as their P operand (for
example, the TNF at card sequence 25670 in the original University of
Oregon listing), which causes Punch Check errors (invalid alphanumeric
codes, printed as "?") whenever IPL-V's own trace facility writes to the
card punch.

This turned out to be a known, documented defect: two update documents
found by Rupert Lane address it directly.

  Modification Letter Number 3
      https://purl.stanford.edu/bk072pk3345
  Modification Letter Number 4
      https://purl.stanford.edu/qg281jn8061

Applying both letters to the interpreter source fixes the Punch Check
errors. Letters 1 and 2 have not been located or applied, so their effects
(if any) on this program are unknown.

Files in this directory
------------------------

IPL-V-Interpreter-Mod-3-4.sps
    SPS assembler source for the interpreter with Modification Letters 3
    and 4 applied, derived from ../IPL-V-Interpreter.sps.

IPL-V-Interpreter-Mod-3-4-Listing.lst
    Assembly listing of the updated source.

IPL-V-Interpreter-Mod-3-4-Object.card
    Compressed object deck assembled from the updated source.

IPL-V-Interpreter-Mod-3-4-Object-UNCOMPRESSED.card
    Uncompressed object deck, used to generate the listing above via
    software/retro-1620-Utilities/SPS-Object-Deck-Lister-LHCode.wsf.

IPL-V-Interpreter-Mod-3-4-Deck-1.card
IPL-V-Interpreter-Mod-3-4-Deck-2.card
    The two-part load deck (assembler/loader, then interpreter), split the
    same way as ../IPL-V-Interpreter-Deck-1.card / -Deck-2.card. Use these
    in place of the originals; ../IPL-V-Subroutines.card is unchanged and
    should still be used from its original location.

Ackermann-TEST.ipl
    A smaller regression case identical to ../Ackermann.ipl except that the
    M0/N0 region constants are set to 1 and 1 (rather than 3 and 3), used
    to study the Ackermann(1,1) failure without the "hoary recursion" of the
    full A(3,3) case.

IPL-V-Punch-Trace-Ack-1-0-20260823.txt
IPL-V-Punch-Trace-Ack-1-1-20260823.txt
    IPL-V's own trace output (not the emulator's instruction trace),
    captured via the 1620 control panel's four Program Switches all set on,
    for Ackermann(1,0) (succeeds, ends with result 2) and Ackermann(1,1)
    (fails -- terminated after it was clearly running away).

Ackermann-1-0-vs-1-1-Trace-20260823.pdf
    A side-by-side comparison of the two traces above.

Status
------

Confirmed independently (2026-09-10) using a new headless CLI harness for
the emulator (tools/cli/run1620.mjs, see the repo root): running
../IPL-V-Interpreter-Deck-1.card/-Deck-2.card (the un-patched decks) with
Ackermann(3,3) and all four Program Switches on reproduces the Punch Check
"?" garbage Paul describes above verbatim. Running the Mod-3-4 decks in
this directory with Ackermann-TEST.ipl (m=1,n=1) and all four switches on
reproduces his IPL-V-Punch-Trace-Ack-1-1-20260823.txt output exactly
(diffed byte-for-byte, aside from a header line), and the m=1,n=0 case
reproduces IPL-V-Punch-Trace-Ack-1-0-20260823.txt exactly as well. So: the
Mod-3-4 patch fixes the Punch Check errors, and does NOT fix the underlying
n>0 problem -- both confirmed exactly as Paul found.

The underlying problem itself is still open. Ackermann(m,n) fails to
complete for any n>0, eventually printing "TRAPPED ON H2" repeatedly.

Per Newell, Tonge, et al., "Information Processing Language-V, Second
Edition" (RAND/Prentice-Hall, 1964) -- a scan of which is available
alongside this repo, though not itself committed here for size/copyright
reasons -- H2 is IPL-V's available-space list: all memory cells not
currently part of any list or routine are linked together on H2, and any
process needing a new cell gets it from there; "TRAPPED ON H2" is what
happens when that request finds the list exhausted. J111/J117/J125/J152
(the primitives Ackermann.ipl calls directly) correspond to 1620-specific
routine numbers assigned in ../IPL-V-Interpreter.sps -- they are not
documented in the general RAND manual, which describes the language's
primitives independent of any particular machine's routine-numbering. Their
1620 assembly (search for JJ111/JJ117/JJ125/JJ152 in
IPL-V-Interpreter-Mod-3-4.sps) shows J125 as an increment-and-pushdown
primitive and J111 as the decrement counterpart, both built on a PSHDN
(push-down) primitive and GET1/GET3 (cell-fetch) primitives with BADIND/
BADSET error paths -- consistent with the manual's pushdown-list
description, but tracing the exact fault through PSHDN/GET1/GET3 has not
been done yet.

An earlier version of this note claimed a specific trace column showed
region K1 (which should hold constant 1) instead reading back as 10000.
That is probably a misreading of the trace format (that column looks more
likely to be the raw content of whatever cell H0 currently points to, not
literally "K1's value" -- the same ~10000-ish figure shows up in the same
position in the successful Ackermann(1,0) trace too), and should not be
relied on without going back through the trace format used at
IPL-V-Interpreter-Listing.lst line ~1873's header (LEVEL CIA HS P Q SYMB
LINK S (0) CONTENTS-OF-(0) H3) to confirm what each column actually is.
What IS a solid, repeatable observation: whatever value ends up in that
"CONTENTS OF (0)" column diverges from a small, sane number to something
~10000 in magnitude at the first recursive descent in every n>0 case, and
then drifts by further ~10000 increments each additional recursion level,
exactly tracking with unbounded recursion depth and the eventual H2
exhaustion. Pinning down which specific instruction introduces that
~10000-ish value, and whether it is a genuine 1620-port bug, an
Ackermann.ipl transcription error, or an emulator bug, needs deliberate
instruction-level tracing through PSHDN/GET1/GET3 (now practical to do
quickly with tools/cli/run1620.mjs's --trace flag, which did not
previously exist) cross-referenced against IPL-V-Interpreter-Mod-3-4-Listing.lst.

One genuine emulator bug was found and fixed in the process: enabling
processor.tracing before the very first LOAD/INSERT crashed
(Processor.enterICycle() called tracePOperand() before opThisAtts was ever
set, since insert() synthesizes the initial RN directly rather than going
through normal instruction decode). Fixed in emulator/Processor.js.

#!/usr/bin/env python3
"""Decode raven4 output. usage: decode.py run.log
Cards: word/successor text = 'Vn 81 TEXT'; counts = '<addr> 01 <n>'; '****' separates
words in the continuation table and ends it; the words after the last mark are the generated text."""
import re, sys
toks = []
for line in open(sys.argv[1]):
    m = re.search(r"\bV?[A-Z]\d+\s+81\s+(\S+)", line)
    if m: toks.append(("t", m.group(1))); continue
    m = re.match(r"\s*\d+\s+01\s+(\d+)\s*$", line)
    if m: toks.append(("n", int(m.group(1))))
marks = [i for i, (k, v) in enumerate(toks) if k == "t" and v == "****"]
if len(marks) < 2: print("no complete table found;", sum(1 for k, _ in toks if k == "t"), "text cards")
else:
    print("CONTINUATION TABLE (word: successor count, ...)")
    for a, b in zip(marks, marks[1:]):
        blk = toks[a + 1:b]
        succ = ["%s %d" % (blk[i][1], blk[i + 1][1]) for i in range(1, len(blk) - 1, 2)]
        print("%-5s: %s" % (blk[0][1], ", ".join(succ)))
    gen = [v for k, v in toks[marks[-1] + 1:] if k == "t"]
    print("\nGENERATED (%d words):" % len(gen)); print(" ".join(gen))
if "TRAPPED" in open(sys.argv[1]).read(): print("\n*** run TRAPPED (error trap) ***")

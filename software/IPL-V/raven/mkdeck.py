#!/usr/bin/env python3
"""Tokenize the first N lines of raven.txt and emit raven3.ipl (+ raven3.vocab).
usage: mkdeck.py [nlines=2] [steps=40] [--table]   (writes raven4.ipl)
Words -> regional symbols T1..Tn (first-seen order); the text is a data list T39;
each word gets an empty successor list named by its own symbol. The IPL-V
program trains (appends each word to its predecessor's list) and generates.
Long explanations go on TYPE-1 comment cards (text in cols 7-40, '1' in col 41)."""
import re, sys, textwrap

def card(comment="", typ="", name="", pq="", symb="", link=""):
    s = [" "] * 80
    def put(col, txt):
        for i, c in enumerate(txt): s[col - 1 + i] = c
    put(7, comment[:34]); put(41, typ); put(43, name); put(49, pq); put(51, symb)
    if link != "": put(57, link)
    return "".join(s).rstrip()

def const(comment, name, value):            # integer data term, value right-justified to col 61
    s = [" "] * 80
    for i, c in enumerate(comment[:34]): s[6 + i] = c
    s[42], s[43], s[48], s[49] = name[0], name[1], "0", "1"
    v = str(value)
    for i, c in enumerate(v): s[61 - len(v) + i] = c
    return "".join(s).rstrip()

args = [a for a in sys.argv[1:] if not a.startswith("--")]
table = "--table" in sys.argv
nlines = int(args[0]) if len(args) > 0 else 2
steps = int(args[1]) if len(args) > 1 else 40
lines = [l for l in open("raven.txt", encoding="utf-8").read().split("\n") if l.strip()][:nlines]
words = re.findall(r"[a-z']+", " ".join(lines).lower())
vocab = {}
for w in words: vocab.setdefault(w, "T%d" % (len(vocab) + 1))
text = [vocab[w] for w in words]
assert len(vocab) < 39
open("raven4.vocab", "w").write("\n".join("%s %s" % (v, w) for w, v in vocab.items()) + "\n")

L = []
def C(*paras):                               # type-1 comment cards, wrapped to 34 cols
    for p in paras:
        for ln in textwrap.wrap(p, 34) or [""]: L.append(card(ln, typ="1"))
def I(pq="", symb="", name="", link="", c=""):
    L.append(card(c, name=name, pq=pq, symb=symb, link=link))

L.append(card("RAVEN4: TRAIN + GENERATE", typ="9"))
C("BIGRAM MARKOV TEXT GENERATOR USING DESCRIPTION LISTS.",
  "TEXT: FIRST %d LINES OF THE RAVEN, %d TOKENS, %d DISTINCT WORDS (SEE RAVEN4.VOCAB)." % (nlines, len(words), len(vocab)),
  "EVERY WORD IS A REGIONAL SYMBOL T1..T%d, AND IS ALSO A DESCRIBABLE LIST (A HEAD CELL, INITIALLY EMPTY)." % len(vocab),
  "A WORD'S DESCRIPTION LIST HOLDS ITS SUCCESSORS: EACH ATTRIBUTE IS A WORD THAT FOLLOWED IT IN THE TEXT, AND ITS VALUE IS AN INTEGER DATA TERM COUNTING HOW OFTEN. ONLY SUCCESSORS ACTUALLY SEEN ARE STORED, SO THE TABLE IS SPARSE.",
  "PHASE 1 (TRAIN): FOR EACH ADJACENT PAIR (PREV, THIS) OF THE TEXT LIST T39, ADD 1 TO THE COUNT OF THIS IN PREV'S DESCRIPTION LIST, CREATING IT WITH COUNT 1 IF IT IS NEW (ROUTINE G2).",
  "PHASE 2 (GENERATE): REPEAT N TIMES: J16 PICKS A SUCCESSOR OF THE CURRENT WORD AT RANDOM, WEIGHTED BY THE COUNTS (ROUTINE G1).",
  "WORKING CELLS (W0-W2 ARE AVOIDED: J11 AND OTHER LIBRARY ROUTINES OVERWRITE THEM): W9 CURRENT WORD, W4 PREVIOUS WORD, W6 CURRENT TEXT CELL, W5 THIS WORD, W7 FIRST WORD, W8 STEP COUNTER.")
L += [card("DEFINE REGIONS", typ="2", name="A0", link="2"),
      card("LIST REGION", typ="2", name="L0", link="300"),
      card("TOKEN REGION", typ="2", name="T0", link="40"),
      card("ROUTINE REGION", typ="2", name="G0", link="4"),
      card("NUMBER REGION", typ="2", name="N0", link="4")]
C("REGION L0 SUPPLIES CELLS FOR THE PUSHDOWN STACK AND FOR THE DESCRIPTION LISTS AND COUNTS BUILT DURING TRAINING.")
L.append(card("ROUTINE HEADER. TYPE=5,Q=0.", typ="5", pq="00"))

C("--- MAIN PROGRAM A0 ---",
  "PHASE 1: TRAIN. START AT THE HEAD CELL OF THE TEXT LIST AND STEP TO ITS FIRST CELL WITH J60 (LOCATE NEXT CELL).")
I("10", "T39", "A0", c="PUSH TEXT LIST HEAD T39")
I(symb="J60", c="J60: (0) = FIRST TEXT CELL")
I("20", "W6", c="W6 = FIRST CELL; POP")
C("READ THE WORD IN THAT CELL WITH J80 (SYMBOL IN CELL); IT IS THE PREVIOUS WORD W4. KEEP A COPY IN W7 SO THE LAST WORD CAN WRAP AROUND TO THE FIRST.")
I("11", "W6", c="PUSH CONTENTS OF W6 (THE CELL)")
I(symb="J80", c="J80: (0) = WORD IN CELL")
I("20", "W4", c="W4 = PREVIOUS WORD; POP")
I("11", "W4"); I("20", "W7", c="W7 = FIRST WORD")
C("TRAINING LOOP, LABEL 9-1. STEP TO THE NEXT TEXT CELL. J60 SETS H5+ IF THERE WAS ONE, H5- AT THE END OF THE LIST; 70 9-9 BRANCHES TO 9-9 WHEN H5-.")
I("11", "W6", "9-1", c="LOOP: PUSH CURRENT CELL")
I(symb="J60", c="J60: (0) = NEXT CELL, SET H5")
I("70", "9-9", c="IF H5-, TEXT ENDED: GO 9-9")
I("20", "W6", c="W6 = NEXT CELL; POP")
I("11", "W6"); I(symb="J80", c="(0) = WORD IN THAT CELL")
I("20", "W5", c="W5 = THIS WORD; POP")
I(symb="G2", c="G2: COUNT PAIR (W4 -> W5)")
I("11", "W5"); I("20", "W4", link="9-1", c="W4 = W5; GO BACK TO 9-1")
C("9-9: TRAINING DONE. J60 LEFT THE LAST CELL ON THE STACK WHEN IT FAILED; J8 POPS IT. THEN CLOSE THE CYCLE BY COUNTING THE PAIR (LAST WORD W4 -> FIRST WORD W7) SO NO WORD IS A DEAD END.")
I(symb="J8", name="9-9", c="POP LEFTOVER CELL")
I("11", "W7"); I("20", "W5", c="W5 = FIRST WORD")
I(symb="G2", c="G2: COUNT PAIR (W4 -> W5)")
if table:
    C("PRINT THE TRAINED TABLE: WALK THE VOCABULARY LIST T38 (LOOP 9-6) AND PRINT EACH WORD WITH J150 (PRINT LIST STRUCTURE), WHICH INCLUDES ITS DESCRIPTION LIST.")
    I("10", "T38"); I(symb="J60"); I("20", "W6", c="W6 = FIRST VOCAB CELL")
    I("11", "W6", "9-6", c="PRINT LOOP: PUSH CELL")
    I(symb="J80", c="(0) = WORD IN CELL")
    I(symb="J150", c="J150: PRINT THE WORD'S LISTS")
    I("11", "W6"); I(symb="J60", c="NEXT VOCAB CELL")
    I("70", "9-7", c="IF H5-, DONE: GO 9-7")
    I("20", "W6", link="9-6", c="W6 = NEXT CELL; LOOP")
    I(symb="J8", name="9-7", c="POP LEFTOVER CELL")
C("PHASE 2: GENERATE. W9 = FIRST WORD; PRINT IT WITH J152 (PRINT SYMBOL).")
I("10", text[0], c="PUSH FIRST WORD"); I("20", "W9", c="W9 = CURRENT WORD; POP")
I("11", "W9"); I(symb="J152", c="PRINT IT")
C("STEP COUNTER W8 IS A FRESH COPY (J120) OF THE CONSTANT ZERO N2, SO J125 (ADD 1) DOES NOT CHANGE THE CONSTANT.")
I("10", "N2"); I(symb="J120", c="J120: COPY OF ZERO"); I("20", "W8", c="W8 = COUNTER = 0")
C("GENERATION LOOP, LABEL 9-2. J116 TESTS (0) < (1): PUSH THE LIMIT N1 FIRST, THEN THE COUNTER. 70 9-3 LEAVES THE LOOP WHEN THE TEST FAILS (H5-).")
I("10", "N1", "9-2", c="LOOP: PUSH LIMIT N1 (=(1))")
I("11", "W8", c="PUSH COUNTER (=(0))")
I(symb="J116", c="J116: H5+ IF COUNTER < LIMIT")
I("70", "9-3", c="IF H5-, DONE: GO 9-3")
I(symb="G1", c="G1: MAKE AND PRINT ONE WORD")
I("11", "W8"); I(symb="J125", c="J125: ADD 1 TO COUNTER, LEAVE (0)")
I(symb="J8", link="9-2", c="J8 POPS (0); GO BACK TO 9-2")
I(symb="J7", name="9-3", link="0", c="9-3: HALT")

L.append(card("ROUTINE HEADER. TYPE=5,Q=0.", typ="5", pq="00"))
C("--- G1: ONE GENERATION STEP ---",
  "INPUT: W9 = CURRENT WORD. OUTPUT: W9 = NEXT WORD, ALSO PRINTED.",
  "J16 TAKES A DESCRIBABLE LIST (THE CURRENT WORD) AND RETURNS ONE OF THE ATTRIBUTES OF ITS DESCRIPTION LIST (A SUCCESSOR WORD), CHOSEN AT RANDOM WITH PROBABILITY PROPORTIONAL TO THE INTEGER COUNT VALUE.")
I("11", "W9", "G1", c="PUSH CURRENT WORD")
I(symb="J16", c="J16: (0) = WEIGHTED RANDOM SUCCESSOR")
I("20", "W9", c="W9 = NEXT WORD; POP")
I("11", "W9"); I(symb="J152", link="0", c="PRINT IT; END OF G1")

L.append(card("ROUTINE HEADER. TYPE=5,Q=0.", typ="5", pq="00"))
C("--- G2: COUNT ONE BIGRAM ---",
  "INPUT: W4 = PREVIOUS WORD, W5 = THIS WORD. EFFECT: THE COUNT OF W5 IN W4'S DESCRIPTION LIST GOES UP BY 1; IT IS CREATED WITH COUNT 1 IF W5 WAS NOT THERE.",
  "J10 = FIND VALUE OF ATTRIBUTE (0) OF LIST (1): PUSH THE LIST W4 FIRST, THEN THE ATTRIBUTE W5. IF FOUND (H5+) THE VALUE, AN INTEGER DATA TERM, IS LEFT AS (0); IF NOT (H5-) NOTHING IS LEFT.")
I("11", "W4", "G2", c="PUSH LIST = PREVIOUS WORD")
I("11", "W5", c="PUSH ATTRIBUTE = THIS WORD")
I(symb="J10", c="J10: FIND COUNT; SET H5")
I("70", "9-5", c="IF H5- (NEW PAIR), GO 9-5")
C("FOUND: J125 ADDS 1 TO THE COUNT IN PLACE AND LEAVES IT AS (0); J8 POPS IT. THEN SKIP THE CREATE STEP.")
I(symb="J125", c="J125: COUNT = COUNT + 1")
I(symb="J8", link="9-6", c="POP COUNT; GO 9-6")
C("9-5 NEW PAIR: J11 = ASSIGN (1) AS VALUE OF ATTRIBUTE (0) OF LIST (2). PUSH LIST W4, THEN A FRESH COPY OF THE CONSTANT ONE N3 (J120 SO THE CONSTANT IS NOT SHARED), THEN THE ATTRIBUTE W5. J11 CREATES THE DESCRIPTION LIST IF IT DOES NOT EXIST YET.")
I("11", "W4", "9-5", c="PUSH LIST (2)")
I("10", "N3"); I(symb="J120", c="J120: NEW COUNT CELL = 1 (1)")
I("11", "W5", c="PUSH ATTRIBUTE (0)")
I(symb="J11", link="0", c="J11: ADD (W5 -> 1) TO W4")
I(symb="J0", name="9-6", link="0", c="9-6: END OF G2 (NO-OP)")

L.append(card("DATA HEADER. TYPE=5,Q=1.", typ="5", pq="01"))
C("DATA. CONSTANTS: N1 = NUMBER OF WORDS TO GENERATE, N2 = ZERO, N3 = ONE.")
L.append(const("N1 = STEPS", "N1", steps)); L.append(const("N2 = ZERO", "N2", 0)); L.append(const("N3 = ONE", "N3", 1))
C("WORD HEADS, ONE PER WORD: AN EMPTY DESCRIBABLE LIST (HEAD CELL, LINK 0) NAMED BY THE WORD SYMBOL. J11 FILLS IN THE DESCRIPTION LIST DURING TRAINING.")
for w, v in vocab.items():
    L.append(card("HEAD OF " + w.upper(), name=v, symb="0", link="0"))
if table:
    C("VOCABULARY LIST T38, USED ONLY TO PRINT THE TABLE.")
    L.append(card("VOCABULARY LIST", name="T38", symb="0"))
    vs = list(vocab.values())
    for k, t in enumerate(vs): L.append(card("", symb=t, link="0" if k == len(vs) - 1 else ""))
C("THE TEXT, AS A LIST OF WORD SYMBOLS, HEAD T39: " + " ".join(words).upper())
L.append(card("TEXT LIST", name="T39", symb="0"))
for k, t in enumerate(text):
    L.append(card("", symb=t, link="0" if k == len(text) - 1 else ""))
L.append(card("START AT A0", typ="5", symb="A0"))
open("raven4.ipl", "w").write("\n".join(L) + "\n")
print(len(words), "tokens,", len(vocab), "distinct,", steps, "steps ->", "raven4.ipl", len(L), "cards")

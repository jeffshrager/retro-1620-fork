#!/usr/bin/env python3
"""Tokenize the first N lines of raven.txt and emit raven3.ipl (+ raven3.vocab).
usage: mkdeck.py [nlines=2] [steps=40]
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

nlines = int(sys.argv[1]) if len(sys.argv) > 1 else 2
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 40
lines = [l for l in open("raven.txt", encoding="utf-8").read().split("\n") if l.strip()][:nlines]
words = re.findall(r"[a-z']+", " ".join(lines).lower())
vocab = {}
for w in words: vocab.setdefault(w, "T%d" % (len(vocab) + 1))
text = [vocab[w] for w in words]
assert len(vocab) < 39
open("raven3.vocab", "w").write("\n".join("%s %s" % (v, w) for w, v in vocab.items()) + "\n")

L = []
def C(*paras):                               # type-1 comment cards, wrapped to 34 cols
    for p in paras:
        for ln in textwrap.wrap(p, 34) or [""]: L.append(card(ln, typ="1"))
def I(pq="", symb="", name="", link="", c=""):
    L.append(card(c, name=name, pq=pq, symb=symb, link=link))

L.append(card("RAVEN3: TRAIN + GENERATE", typ="9"))
C("BIGRAM MARKOV TEXT GENERATOR.",
  "TEXT: FIRST %d LINES OF THE RAVEN, %d TOKENS, %d DISTINCT WORDS (SEE RAVEN3.VOCAB)." % (nlines, len(words), len(vocab)),
  "EVERY WORD IS A REGIONAL SYMBOL T1..T%d. A WORD'S OWN SYMBOL NAMES ITS SUCCESSOR LIST: THE LIST OF WORDS THAT FOLLOWED IT IN THE TEXT. A WORD THAT FOLLOWED IT TWICE APPEARS TWICE, SO THE COUNT IS THE NUMBER OF REPEATS." % len(vocab),
  "PHASE 1 (TRAIN): WALK THE TEXT LIST T39 AND APPEND EACH WORD TO THE LIST OF THE WORD BEFORE IT.",
  "PHASE 2 (GENERATE): PRINT THE TABLE, THEN REPEAT N TIMES: PICK A RANDOM WORD FROM THE CURRENT WORD'S LIST, PRINT IT, MAKE IT CURRENT.",
  "WORKING CELLS: W0 CURRENT WORD, W1 PREVIOUS WORD, W2 CURRENT TEXT CELL, W3 THIS WORD, W4 FIRST WORD, W5 STEP COUNTER.")
L += [card("DEFINE REGIONS", typ="2", name="A0", link="2"),
      card("LIST REGION", typ="2", name="L0", link="200"),
      card("TOKEN REGION", typ="2", name="T0", link="40"),
      card("GENERATOR STEP REGION", typ="2", name="G0", link="2"),
      card("NUMBER REGION", typ="2", name="N0", link="4")]
C("REGION L0 SUPPLIES LIST CELLS FOR THE PUSHDOWN STACK AND FOR THE NEW SUCCESSOR ENTRIES.")
L.append(card("ROUTINE HEADER. TYPE=5,Q=0.", typ="5", pq="00"))

C("--- MAIN PROGRAM A0 ---",
  "PHASE 1: TRAIN. START AT THE HEAD CELL OF THE TEXT LIST AND STEP TO ITS FIRST CELL WITH J60 (LOCATE NEXT CELL).")
I("10", "T39", "A0", c="PUSH TEXT LIST HEAD T39")
I(symb="J60", c="J60: (0) = FIRST TEXT CELL")
I("20", "W2", c="W2 = FIRST CELL; POP")
C("READ THE WORD IN THAT CELL WITH J80 (SYMBOL IN CELL) AND REMEMBER IT AS THE PREVIOUS WORD W1. ALSO KEEP A COPY IN W4 SO THE LAST WORD CAN WRAP AROUND TO THE FIRST AT THE END.")
I("11", "W2", c="PUSH CONTENTS OF W2 (THE CELL)")
I(symb="J80", c="J80: (0) = WORD IN CELL")
I("20", "W1", c="W1 = PREVIOUS WORD; POP")
I("11", "W1"); I("20", "W4", c="W4 = FIRST WORD")
C("TRAINING LOOP, LABEL 9-1. STEP TO THE NEXT TEXT CELL. J60 SETS H5+ IF THERE WAS ONE, H5- AT THE END OF THE LIST; 70 9-9 BRANCHES TO 9-9 WHEN H5-.")
I("11", "W2", "9-1", c="LOOP: PUSH CURRENT CELL")
I(symb="J60", c="J60: (0) = NEXT CELL, SET H5")
I("70", "9-9", c="IF H5-, TEXT ENDED: GO 9-9")
I("20", "W2", c="W2 = NEXT CELL; POP")
I("11", "W2"); I(symb="J80", c="(0) = WORD IN THAT CELL")
I("20", "W3", c="W3 = THIS WORD; POP")
C("APPEND THIS WORD TO THE SUCCESSOR LIST OF THE PREVIOUS WORD. J65 = INSERT (0) AT END OF LIST (1), SO PUSH THE LIST NAME (W1) FIRST, THEN THE WORD (W3). THEN THIS WORD BECOMES THE PREVIOUS WORD.")
I("11", "W1", c="PUSH PREV WORD = LIST NAME (1)")
I("11", "W3", c="PUSH THIS WORD = (0)")
I(symb="J65", c="J65: APPEND W3 TO LIST W1")
I("11", "W3"); I("20", "W1", link="9-1", c="W1 = W3; GO BACK TO 9-1")
C("9-9: TRAINING DONE. J60 LEFT THE LAST CELL ON THE STACK WHEN IT FAILED; J8 POPS IT. THEN CLOSE THE CYCLE BY APPENDING THE FIRST WORD (W4) TO THE LIST OF THE LAST WORD (W1) SO NO WORD IS A DEAD END.")
I(symb="J8", name="9-9", c="POP LEFTOVER CELL")
I("11", "W1"); I("11", "W4"); I(symb="J65", c="APPEND FIRST WORD TO LAST WORD'S LIST")
C("PRINT THE TRAINED TABLE: J151 PRINTS EACH SUCCESSOR LIST (HEAD LINE, THEN ONE SUCCESSOR PER LINE).")
for v in vocab.values():
    I("10", v); I(symb="J151")
C("PHASE 2: GENERATE. W0 = FIRST WORD; PRINT IT WITH J152 (PRINT SYMBOL).")
I("10", text[0], c="PUSH FIRST WORD"); I("20", "W0", c="W0 = CURRENT WORD; POP")
I("11", "W0"); I(symb="J152", c="PRINT IT")
C("STEP COUNTER W5 IS A FRESH COPY (J120) OF THE CONSTANT ZERO N2, SO J125 (ADD 1) DOES NOT CHANGE THE CONSTANT.")
I("10", "N2"); I(symb="J120", c="J120: COPY OF ZERO"); I("20", "W5", c="W5 = COUNTER = 0")
C("GENERATION LOOP, LABEL 9-2. J116 TESTS (0) < (1): PUSH THE LIMIT N1 FIRST, THEN THE COUNTER. 70 9-3 LEAVES THE LOOP WHEN THE TEST FAILS (H5-).")
I("10", "N1", "9-2", c="LOOP: PUSH LIMIT N1 (=(1))")
I("11", "W5", c="PUSH COUNTER (=(0))")
I(symb="J116", c="J116: H5+ IF COUNTER < LIMIT")
I("70", "9-3", c="IF H5-, DONE: GO 9-3")
I(symb="G1", c="G1: MAKE AND PRINT ONE WORD")
I("11", "W5"); I(symb="J125", c="J125: ADD 1 TO COUNTER, LEAVE (0)")
I(symb="J8", link="9-2", c="J8 POPS (0); GO BACK TO 9-2")
I(symb="J7", name="9-3", link="0", c="9-3: HALT")

L.append(card("ROUTINE HEADER. TYPE=5,Q=0.", typ="5", pq="00"))
C("--- G1: ONE GENERATION STEP ---",
  "INPUT: W0 = CURRENT WORD. OUTPUT: W0 = NEXT WORD, ALSO PRINTED.",
  "THE CURRENT WORD'S OWN SYMBOL NAMES ITS SUCCESSOR LIST. PUSH IT TWICE: THE TOP COPY IS CONSUMED BY THE COUNT, THE LOWER COPY IS THE LIST NAME (1) THAT J200 LATER SEARCHES.")
I("11", "W0", "G1", c="PUSH CURRENT WORD = LIST NAME")
I("11", "W0", c="PUSH IT AGAIN")
I(symb="J126", c="J126: (0) = N, LENGTH OF LIST")
I(symb="J129", c="J129: (0) = RANDOM R, 0 <= R < N")
I(symb="J125", c="J125: R+1 (J200 COUNTS FROM 1)")
I(symb="J200", c="J200: (0) = THE (R+1)TH CELL")
I(symb="J80", c="J80: (0) = WORD IN THAT CELL")
I("20", "W0", c="W0 = NEXT WORD; POP")
I("11", "W0"); I(symb="J152", link="0", c="PRINT IT; END OF G1")

L.append(card("DATA HEADER. TYPE=5,Q=1.", typ="5", pq="01"))
C("DATA. CONSTANTS: N1 = NUMBER OF WORDS TO GENERATE, N2 = ZERO.")
L.append(const("N1 = STEPS", "N1", steps)); L.append(const("N2 = ZERO", "N2", 0))
C("SUCCESSOR LISTS, ONE PER WORD, EMPTY UNTIL TRAINED: A HEAD CELL NAMED BY THE WORD, LINK 0 = NO CELLS.")
for w, v in vocab.items():
    L.append(card("SUCCESSORS OF " + w.upper(), name=v, symb="0", link="0"))
C("THE TEXT, AS A LIST OF WORD SYMBOLS, HEAD T39: " + " ".join(words).upper())
L.append(card("TEXT LIST", name="T39", symb="0"))
for k, t in enumerate(text):
    L.append(card("", symb=t, link="0" if k == len(text) - 1 else ""))
L.append(card("START AT A0", typ="5", symb="A0"))
open("raven3.ipl", "w").write("\n".join(L) + "\n")
print(len(words), "tokens,", len(vocab), "distinct,", steps, "steps ->", "raven3.ipl", len(L), "cards")

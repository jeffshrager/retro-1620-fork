raven/ -- bigram Markov text generator in IPL-V (trained on THE RAVEN)

HOW TO RUN (GUI or CLI): card reader deck order
   1. software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-1.card
   2. rave.ipl   (or raven4.ipl = same program with comment cards)
   3. software/IPL-V/IPL-V-Subroutines.card
   4. software/IPL-V/Mod-3-4/IPL-V-Interpreter-Mod-3-4-Deck-2.card
Core memory 40000 digits is enough for the default 12-line build.

MUST use the Mod-3-4 interpreter decks. With the original decks, printing an
alphanumeric data term punches "??+" (Punch Check, the TNF odd-address bug) and
the run dies, e.g. one card "K2 ??+ ****" and an arithmetic check.

Cards may contain only the characters the GUI card reader accepts: uppercase
A-Z, 0-9, space and  . ) + $ * - / , ( = @ | } ! "   (no  : ; < > [ ] '  or
lowercase). mkdeck.py sanitizes its comments; the CLI warns about bad cards.

Files: mkdeck.py builds the deck from raven.txt
          python3 mkdeck.py [nlines=12] [steps=100] [--lspace=900] [--no-table]
                            [--no-comments] [--out=raven4.ipl]
       decode.py run.log   turns the punched cards into the continuation table
                           and the generated text (words are printed as pieces)
       raven4_decoded.txt  a saved result;  log.md  the experiment log

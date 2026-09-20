# Regenerate manual.txt / manual_flow.txt from the manual PDF in this folder.
# Needs PyMuPDF: python3 -m venv /tmp/v && /tmp/v/bin/pip install pymupdf && /tmp/v/bin/python pdf2txt.py
import glob, re, pymupdf
pdf = [p for p in glob.glob("*Newell*.pdf")][0]
pages = [f"\n===== PDF PAGE {i} =====\n" + pg.get_text() for i, pg in enumerate(pymupdf.open(pdf), 1)]
open("manual.txt", "w", encoding="utf-8").write("".join(pages))
flow = [re.sub(r"\s*\n\s*", " ", p.split("=====\n", 1)[1]).strip() for p in pages]
open("manual_flow.txt", "w", encoding="utf-8").write("".join(f"\n===== PDF PAGE {i} =====\n{b}\n" for i, b in enumerate(flow, 1)))

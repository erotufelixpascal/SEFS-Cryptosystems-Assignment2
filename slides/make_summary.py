"""Build the 10-slide summary deck from the full deck.

    python make_summary.py            (needs python-pptx: pip install python-pptx)

Keeps the slides listed in KEEP (1-based numbers in the full deck), removes the rest,
renumbers the page numbers and relabels the title slide. Rerun it after rebuilding the
full deck with build_slides.js; check KEEP if slides were added or moved.
"""

import re
import shutil
from pptx import Presentation

SOURCE = "Group 6 SEFS Progress v8.pptx"
OUT = "Group 6 SEFS Summary (10 slides).pptx"

KEEP = [
    1,   # title
    2,   # where the project stands
    5,   # layered design
    9,   # end-to-end flows
    11,  # security goals (CIA)
    13,  # passwords: salt + slow hash (Part 1)
    24,  # tampering simulation (Parts 2-3)
    34,  # result: 70% vs 25%
    35,  # detection by area
    41,  # conclusions
]

shutil.copyfile(SOURCE, OUT)
prs = Presentation(OUT)
sld_id_lst = prs.slides._sldIdLst
ids = list(sld_id_lst)
assert len(ids) >= max(KEEP), f"{SOURCE} has only {len(ids)} slides"

removed = set()
for n, sld in enumerate(ids, 1):
    if n not in KEEP:
        removed.add(sld.get("id"))
        prs.part.drop_rel(sld.rId)
        sld_id_lst.remove(sld)

# Drop the removed slides from the section list too (and any section left empty).
root = prs.part._element
for el in list(root.iter()):
    if el.tag.endswith("}sldId") and el.get("id") in removed and el.getparent() is not sld_id_lst:
        el.getparent().remove(el)
for sec in list(root.iter()):
    if sec.tag.endswith("}section"):
        lst = [c for c in sec if c.tag.endswith("}sldIdLst")]
        if lst and len(lst[0]) == 0:
            sec.getparent().remove(sec)

# Renumber the page numbers (small digit-only text boxes at the bottom) and relabel slide 1.
for n, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        text = sh.text_frame.text
        if re.fullmatch(r"\d+", text.strip()) and sh.top is not None and sh.top > prs.slide_height * 0.9:
            sh.text_frame.paragraphs[0].runs[0].text = str(n)
        if "PROGRESS UPDATE" in text:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = r.text.replace("PROGRESS UPDATE", "PROJECT SUMMARY")

prs.save(OUT)
print(f"wrote {OUT}: {len(prs.slides)} slides")

"""Build the 13-slide summary deck from the full deck.

    python make_summary.py            (needs python-pptx: pip install python-pptx)

Keeps the slides whose title starts with one of the entries in KEEP (in the full deck's
order), removes the rest, renumbers the page numbers and relabels the title slide.
Slides are found by title, so rebuilding the full deck with build_slides.js does not
break the selection; only a renamed slide title does.
"""

import re
import shutil
from pptx import Presentation

SOURCE = "Group 6 SEFS Progress v9.pptx"
OUT = "Group 6 SEFS Summary.pptx"

KEEP = [
    "SEFS: a Secure Encrypted File System",   # title
    "Introduction and objectives",
    "Where the project stands",
    "Layered design",
    "End-to-end flows",
    "Security goals",
    "Tampering simulation",
    "Methodology",
    "Result: AI-assisted",
    "Results in full",
    "Project intent vs what we delivered",
    "How far the result can be trusted",      # threats to validity
    "Conclusions",
]

shutil.copyfile(SOURCE, OUT)
prs = Presentation(OUT)
sld_id_lst = prs.slides._sldIdLst


def matches(slide):
    texts = [sh.text_frame.text.strip() for sh in slide.shapes if sh.has_text_frame]
    return [k for k in KEEP if any(t.startswith(k) for t in texts)]


found = set()
removed = set()
for slide, sld in zip(list(prs.slides), list(sld_id_lst)):
    m = matches(slide)
    if m:
        found.update(m)
    else:
        removed.add(sld.get("id"))
        prs.part.drop_rel(sld.rId)
        sld_id_lst.remove(sld)
missing = [k for k in KEEP if k not in found]
assert not missing, f"slides not found in {SOURCE}: {missing}"

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

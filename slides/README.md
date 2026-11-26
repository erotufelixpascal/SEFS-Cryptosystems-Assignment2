# Slides

| File | What it is |
|---|---|
| `Group 6 SEFS Progress v10.pptx` | Current deck (45 slides): introduction and objectives, methodology, full system design and flow, Parts 1–3, security goals (CIA), extension experiment, full results table (from analysis/results.md) and conclusions. Built without layout placeholders or theme colours, so it displays the same in PowerPoint, WPS Office and previews |
| `Group 6 SEFS Progress v9.pptx` | Earlier deck: first version with introduction, methodology (inside the extension section) and full results |
| `Group 6 SEFS Progress v8.pptx` | Earlier deck (42 slides) |
| `Group 6 SEFS Progress v7.pptx` | Earlier deck |
| `Group 6 SEFS Progress v6.pptx` | Earlier deck: Parts 1–3, security goals (CIA) |
| `Group 6 SEFS Progress v5.pptx` | Earlier deck: Parts 1 and 2 |
| `Group 6 SEFS Progress v4.pptx` | Previous progress review, kept for reference |
| `Group 6 SEFS Summary v10.pptx` | Current short version (13 slides) of v10: introduction and objectives, methodology, status, design, CIA, tampering, results, intent vs delivered, threats to validity, conclusions. Rebuild with `python make_summary.py` (needs python-pptx); slides are picked by title |
| `Group 6 SEFS Summary v9.pptx` | Earlier short version (13 slides) of v9 |
| `Group 6 SEFS Summary v8.pptx` | Earlier short version (10 slides) of v8 |
| `build_slides.js` | Generates the current deck. Edit this, not the .pptx |

## Updating the deck when a part is finished

1. In `build_slides.js`, set the part's flag in `DONE` to `true` .
2. Update that part's line in `STATUS` (state `"done"` and its detail text).
3. Bump the version in `OUT` (for example `v11`), so earlier decks are kept, never overwritten.
4. Rebuild from this folder:

   ```
   npm install        # first time only
   node build_slides.js
   ```

5. Set `SOURCE` in `make_summary.py` to the new deck and run `python make_summary.py`. The summary gets the same version number (`Group 6 SEFS Summary v11.pptx`).

The status slide, test chart and "Next steps" list update automatically from the `DONE` flags. Slides for Part 4 have not been written yet.

Edits made directly in PowerPoint are lost on the next rebuild, so make lasting changes in `build_slides.js`.

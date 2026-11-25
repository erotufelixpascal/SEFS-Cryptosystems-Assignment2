# Slides

| File | What it is |
|---|---|
| `Group 6 SEFS Progress v8.pptx` (+ `.pdf`) | Current deck (42 slides): full system design and flow, Parts 1–3, security goals (CIA), extension experiment, results and conclusions. Built without layout placeholders or theme colours, so it displays the same in PowerPoint, WPS Office and previews |
| `Group 6 SEFS Progress v7.pptx` (+ `.pdf`) | Earlier deck |
| `Group 6 SEFS Progress v6.pptx` | Earlier deck: Parts 1–3, security goals (CIA) |
| `Group 6 SEFS Progress v5.pptx` | Earlier deck: Parts 1 and 2 |
| `Group 6 SEFS Progress v4.pptx` | Previous progress review, kept for reference |
| `build_slides.js` | Generates the current deck. Edit this, not the .pptx |

## Updating the deck when a part is finished

1. In `build_slides.js`, set the part's flag in `DONE` to `true` .
2. Update that part's line in `STATUS` (state `"done"` and its detail text).
3. Bump the version in `OUT` (for example `v6`).
4. Rebuild from this folder:

   ```
   npm install        # first time only
   node build_slides.js
   ```

The status slide, test chart and "Next steps" list update automatically from the `DONE` flags. Slides for Part 4 and the extension have not been written yet.

Edits made directly in PowerPoint are lost on the next rebuild, so make lasting changes in `build_slides.js`.

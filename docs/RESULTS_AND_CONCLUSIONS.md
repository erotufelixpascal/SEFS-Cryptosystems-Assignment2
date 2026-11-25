# Results and conclusions: AI-assisted vs manual test generation

**Group 6** · Pascal Felix Erotu (fault author) · Daniel Odong (tester) · system under test: `sefs-v1.0`
**Data:** [`analysis/results.md`](../analysis/results.md) and the CSV files next to it · **Logs:** [`logs/`](../logs) · **Design:** [EXPERIMENT.md](EXPERIMENT.md) · **Slides:** `slides/Group 6 SEFS Progress v7.pptx`

## 1. Answer

> **Research question:** Does AI-assisted test generation find more implementation defects than manually designed tests under a fixed time budget?

**In this experiment, yes.** The AI-assisted suite detected **14 of 20** seeded faults (70%); the manual suite detected **5 of 20** (25%). The AI-assisted suite caught every fault the manual suite caught, plus nine more, and needed less of the tester's time. The difference is **+45 percentage points** (95% bootstrap CI +25 to +65), and McNemar's exact test gives **p = 0.0039**, so H0 (equal detection) is rejected.

The result describes this setting (one beginner tester, one AI run, 20 faults); section 6 lists the limits.

## 2. What was compared

| Arm | Who writes the tests | Tests | Tester time |
|---|---|---|---|
| `manual` | Daniel, by hand, no AI | 8 | 160 min (120 budget + 40 over) |
| `ai/run1` | A fresh Claude Opus 5.5 agent, limited to the isolated workspace, answered the 5 standard prompts; Daniel reviewed the tests in a group walkthrough | 132 functions, 340 cases | 50 min (45 walkthrough + 5 fix); generation took 6.5 min of machine time, not counted |
| `manual_extended` | Daniel, extra tests written after the budget | 5 | 100 min |

**Evaluation set:** 20 seeded faults written by the fault author, 5 per area (authentication, round trip, chunk boundaries, tamper), kept hidden from the tester and the AI until scoring. A fault counts as detected when at least one test fails on a copy of the code containing it (`tools/run_mutants.py`). Every suite passed on the unchanged code first.

## 3. Results

| Measure | manual | AI-assisted | manual extended |
|---|---|---|---|
| Seeded faults detected | 5/20 (25%) | **14/20 (70%)** | 0/20 (0%) |
| 95% CI of the detection rate | 11–47% | 48–86% | 0–16% |
| Line coverage of `src/sefs` | 70.9% | **87.7%** | 36.8% |
| Branch coverage | 47.1% | **77.3%** | 9.7% |
| False-positive test failures | 5 | 1 | 0 |
| Real defects found in the unchanged code | 0 | 0 | 0 |
| Tester time | 160 min | 50 min | 100 min |
| Faults detected per tester hour | 1.9 | **16.8** | 0 |

**AI-assisted vs manual, fault by fault:** both caught 5, only the AI-assisted suite caught 9, only the manual suite caught 0, neither caught 6.

**By area** (5 faults each, so one fault = 20 points):

| Area | manual | AI-assisted |
|---|---|---|
| Authentication | 0% | 80% |
| Round trip | 20% | 100% |
| Chunk boundaries | 60% | 60% |
| Tamper | 20% | 40% |

**AI prompt and review log** (`logs/ai_prompt_log.csv`, `logs/ai_review_sheet.csv`): 5 prompts, 132 tests proposed, 131 accepted, 1 edited, 0 rejected. The edited test expected `b"world"` from position 10 of `hello SEFS world`; position 10 is the space, so the test was wrong (false positive D-006).

**Faults no arm detected:** M04 (deleting a user also removes users whose names start the same), M13 (a short middle chunk or wrong link is accepted), M14 (a size field of 1,025–1,076 is accepted), M18 (extra data in the chunks is returned), M19 (a chunk file with bytes appended is accepted), M20 (a changed padding byte is not noticed).

## 4. Interpretation

1. **AI assistance gave breadth.** The AI systematically tried boundary lengths, odd characters and store-then-read-back checks. That is where its lead comes from: authentication (0% → 80%) and round trips (20% → 100%).
2. **The manual suite was narrow.** Several manual tests were "fixed" by changing their expected values, so they ended up checking only that invalid names are rejected. Only the chunk-boundary area, where the manual tests stored real multi-chunk files, matched the AI (60% each).
3. **Coverage is not the same as detection.** The AI suite ran 88% of the lines but still missed 6 faults. Each of those needs a test that hand-crafts a subtly broken file and checks the exact response.
4. **Review is still needed.** One AI test was wrong, and it was found only because a person checked the failing run against the specification.

## 5. Intent vs delivered

| Intended (project brief) | Delivered |
|---|---|
| Research question | Answered for this setting: 70% vs 25%, p = 0.004 |
| AI proposes tests for authentication, round trips, chunk boundaries and tamper handling | 5 standard prompts; 132 test functions across all four areas (`tests/ai/run1/`) |
| Manually validate each generated test | 45-min group walkthrough by the tester; 1 corrected, 131 accepted |
| Compare test coverage | 71% vs 88% lines, 47% vs 77% branches |
| Compare valid defects discovered | 5 vs 14 of 20 seeded faults; 0 real defects in the unchanged code |
| Compare false-positive test failures | 5 manual vs 1 AI (`logs/defect_log.csv`) |
| Compare time spent | 160 vs 50 tester minutes, estimated (`logs/time_log.csv`) |
| Retain an AI prompt/review log | `logs/ai_prompt_log.csv`, `logs/ai_review_sheet.csv` |
| Unique output: AI-assisted regression test suite | `tests/ai/run1/`: 340 cases, all passing on `sefs-v1.0` |
| Unique output: controlled evaluation | Frozen code, hidden faults, isolated AI workspace, manual arm first, statistics in `analysis/` |

## 6. Threats to validity

- **Small study:** one tester, one AI run, 20 faults. The confidence intervals are wide, and the result does not generalise on its own.
- **Beginner tester:** Daniel had no IT background; an experienced tester would probably narrow the gap.
- **Estimated times:** no session was timed. The manual arm went 40 minutes over its 120-minute budget; the AI arm stayed under it.
- **AI arm deviations:** the tests came from an isolated Claude Opus 5.5 agent in Claude Code instead of the planned claude.ai chat, and the review was one group walkthrough rather than test by test.
- **AI assistance in the set-up:** the fault locations were suggested by an AI assistant and fault M01 was AI-written (the other 19 bugs were written by the fault author). The tester's instructions and fill-in-the-blank examples were AI-prepared.
- **Uneven test counts:** 8 manual tests vs 340 AI cases; the AI's volume is part of the effect being measured, not something controlled for.

## 7. Conclusions and recommendations

1. **AI-assisted test generation found significantly more seeded defects than manual testing, in less tester time.**
2. **Its advantage is breadth:** systematic boundaries and input variations that a beginner does not write by hand.
3. **A person must still review AI tests:** one in 132 was wrong.
4. **Neither approach is complete:** six subtle faults escaped every arm.

**Recommendations:** use AI to draft a broad regression suite and review every test against the specification; add hand-written tests for the six missed faults; and repeat the study with a second AI run (`ai/run2`) and a second tester, timing every session.

## 8. Reproduce

```powershell
python tools\run_mutants.py --tests tests\manual
python tools\run_mutants.py --tests tests\manual_extended
python tools\run_mutants.py --tests tests\ai\run1
python tools\measure_coverage.py --tests tests\manual --html          # and the other two arms
python analysis\analyze.py --arms manual manual_extended ai/run1
```

The seeded faults (`mutants/*.toml`) are not in the repository; they are needed to rerun the scoring.

# Group 6 extension: AI-assisted vs. manual test generation (25 marks)

**Tests:** [`tests/manual/`](../tests/manual) · [`tests/ai/run1/`](../tests/ai/run1) · **Faults:** [`mutants/`](../mutants/README.md) · **Tools:** [`tools/`](../tools) · **Analysis:** [`analysis/analyze.py`](../analysis/analyze.py) · **Logs:** [`logs/`](../logs) · **Status:** not started

> Start only once the SEFS implementation passes its tests (`python -m pytest tests\acceptance tests\format` → 18 passed). The brief requires this.

---

## 1. Research question and hypotheses

> **RQ:** Under a fixed time budget, does AI-assisted test generation find more implementation defects in a cryptographic file system than manually designed tests?

- **H0:** the AI-assisted suite and the manual suite detect the same proportion of seeded faults.
- **H1:** the proportions differ (two-sided).

Secondary questions: does either arm achieve higher line/branch coverage; which arm produces more false-positive test failures; how much AI output must be rejected or edited; and where (by area) each arm is strong or weak.

## 2. What is measured

The brief asks for coverage, valid defects discovered, false-positive test failures, time spent, and an AI prompt/review log.

| Brief's measure | Operationalised as | Source |
|---|---|---|
| Valid defects discovered | (a) **Mutation score**: % of hidden seeded faults the suite detects (primary outcome). (b) Real defects found in the unmodified code | `tools/run_mutants.py`; `logs/defect_log.csv` (`real_defect`) |
| Test coverage | Line and branch coverage of `src/sefs/` | `tools/measure_coverage.py` (coverage.py) |
| False-positive test failures | Tests that failed on correct code because the test was wrong | `logs/defect_log.csv` (`false_positive`) |
| Time spent | Minutes per arm; faults detected per hour | `logs/time_log.csv` |
| AI prompt/review log | Every prompt, tests proposed / accepted / edited / rejected, why rejected, review minutes | `logs/ai_prompt_log.csv` |
| Detection by area | Mutation score per area: `authentication`, `round_trip`, `chunk_boundaries`, `tamper` | fault `area` field |

Seeded faults are needed because the real defects in a small, already-tested system are too few to compare two suites; the faults give a known, fixed set of bugs that both arms are scored against.

**Data:** the experiment uses no real or personal data. Each test creates its own synthetic users and file contents in a fresh temporary folder (the `sefs` fixture in [`tests/conftest.py`](../tests/conftest.py)).

**Leakage control** (the analogue of train/test separation here): the seeded faults are the held-out evaluation set. Testers never see them, neither arm sees the other arm's tests, and neither arm sees `tests/acceptance/`.

## 3. Design

| Element | Choice |
|---|---|
| System under test | `sefs-v1.0`: `src/sefs/` frozen with a git tag before any test is written |
| Arm A (baseline) | `manual`: tests written by hand, **no AI of any kind** |
| Arm B | `ai/run1` (optionally `ai/run2`, `ai/run3`): tests proposed by an AI assistant, each run and checked against the specification by a person before it is accepted |
| Budget | **120 minutes per arm** (agreed 2026-11-24), fixed before starting |
| AI tool | **Claude (claude.ai chat)**, a fresh chat per run, opened only on the isolated workspace's prompts; record the model name shown in the chat and the date |
| Inputs to both arms | `docs/` and `tests/conftest.py` only |
| Evaluation set | Seeded faults written by the fault author, hidden until scoring |
| Order | Manual arm first, so AI suggestions cannot influence it |

### Roles

| Role | Does | Must not |
|---|---|---|
| Fault author: **Pascal Felix Erotu** | Writes `mutants/*.toml`; keeps them private | See or write tests before scoring |
| Tester: **Daniel Odong** | Writes both suites; keeps the logs | Open `mutants/` (except `examples/`) or `tests/acceptance/` before scoring |

Roles agreed 2026-11-24. With two students, one is the fault author and the other the tester; each keeps their own code, evidence and analysis. With one student, ask the lecturer how to handle the fault author role and report it as a threat to validity.

## 4. Step by step

### Step 0: prepare (once)

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests\acceptance tests\format -q    # 18 passed
git init; git add -A; git commit -m "SEFS v1.0"; git tag sefs-v1.0
```

Agree the budget and the AI tool and version, and write them in section 3.

Practice the scoring with the example faults:

```powershell
python tools\run_mutants.py --tests tests\acceptance --mutants-dir mutants\examples
Remove-Item analysis\mutants_acceptance.csv
```

### Step 1: seeded faults (fault author, no AI)

Write at least 20 faults, 5 or more per area, as described in [`mutants/README.md`](../mutants/README.md). Check each one applies (`build_error` means it doesn't). Keep them away from the tester.

### Step 2: manual arm (tester, no AI)

Detailed walkthrough: [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md).

1. Turn off every AI feature, including Copilot and editor completion.
2. Write tests in `tests/manual/` from `docs/` only.
3. Log each session in `logs/time_log.csv`: `2026-11-20,Student A,manual,chunk boundary tests,45`
4. Stop when the budget is used up.
5. Run `python -m pytest tests\manual -v` on the clean code. For every failure, decide whether the bug is in `src/` or in the test, and log it in `logs/defect_log.csv`:
   `D-001,2026-11-20,Student A,manual,test_chunks.py::test_x,write_to_file,What went wrong,real_defect,Reported; not fixed until scoring is done`
   Remove or fix `false_positive` tests. **Don't** fix real defects in `src/` until both arms are scored.

### Step 3: AI arm

1. Build an isolated workspace **outside** the project, so the AI cannot read `mutants/`, `tests/acceptance/`, `tests/manual/` or `src/`:
   ```powershell
   python tools\prepare_ai_run.py --run run1
   ```
   This creates `..\SEF_ai_workspace\run1\` with `CONTEXT.md` (the same docs the manual arm used, plus `conftest.py`), `CLAUDE.md` (rules for the AI), `PROMPTS.md` (the five standard prompts and the review steps) and `proposed\`.
2. Start a **fresh** AI session **in that workspace folder**, e.g. a new terminal: `cd ..\SEF_ai_workspace\run1; claude`. Never reuse a session that has seen the project.
3. Before each prompt, reserve its id with `python tools\log_prompt.py next`. Send the standard prompts from `PROMPTS.md` in order.
4. Copy each proposed file into `tests/ai/run1/`, run it, and check every test against the specification **before** accepting it. Tag kept tests `# source: P-001` (add `(edited)` if you changed it).
5. Log the prompt once it is reviewed:
   ```powershell
   $env:SEFS_AI_TOOL = "Claude Opus 5.5"
   python tools\log_prompt.py add --run ai/run1 --area chunk_boundaries --prompt-number 3 --proposed 8 --accepted 5 --edited 2 --rejected 1 --reason "asserted a placeholder padding byte" --minutes 14
   ```
   Use `--prompt "exact text"` instead of `--prompt-number` for any prompt that isn't one of the standard five.
6. Log time with `arm` = `ai/run1`; stop at the budget, including prompting and review time.
7. Run `python -m pytest tests\ai\run1 -v`; log failures in `defect_log.csv` as in Step 2.
8. For more runs: `python tools\prepare_ai_run.py --run run2`, a new session, and `tests/ai/run2/`.

### Step 4: score

Preconditions: both suites pass on clean code (the runner checks this and refuses otherwise), and the fault author has copied the faults into `mutants/`.

```powershell
python tools\run_mutants.py --tests tests\manual
python tools\run_mutants.py --tests tests\ai\run1
```

| Result | Meaning | Counted as |
|---|---|---|
| `detected` | at least one test failed (or the suite timed out) | caught |
| `missed` | all tests passed | missed |
| `build_error` | the fault's edit doesn't apply or has a syntax error | excluded; fault author fixes it |
| `run_error` | pytest could not run | excluded; fix and rerun |

### Step 5: coverage

```powershell
python tools\measure_coverage.py --tests tests\manual --html
python tools\measure_coverage.py --tests tests\ai\run1 --html
```

### Step 6: analyse

```powershell
python analysis\analyze.py
```

| Output | Contents |
|---|---|
| `results_table.csv` | Per arm: tests, faults detected, mutation score with 95% Wilson CI, line and branch coverage, real defects, false positives, minutes, faults/hour, AI prompt totals |
| `statistics.csv` | Manual vs each AI arm: discordant pairs, McNemar's exact p, paired bootstrap 95% CI of the score difference |
| `results_by_area.csv` | Detection % per area per arm |
| `results_by_fault.csv` | Each fault with each arm's result and the test that caught it |
| `results.md` | All tables in Markdown, ready to paste |
| `fig_detection_by_area.png` | Bar chart |

Only faults scored in every arm count, so all arms share one denominator. The bootstrap uses a fixed seed (`--seed`, default 2026) so the numbers are reproducible.

## 5. Rules that keep the experiment valid

- No AI in the manual arm or in writing the faults.
- The tester doesn't see the faults before scoring.
- Same budget, same specification, same `sefs-v1.0` for every arm; `src/` doesn't change between scoring the arms.
- Logs are filled in while working, not reconstructed afterwards.
- Every accepted AI test carries its `# source: P-xxx` tag.
- Report the numbers you measured, including results that don't favour AI.

## 6. Threats to validity (for the report)

- **Low power:** with ~20 faults, only large differences reach significance. Report the CIs, not just p-values.
- **Learning effect:** the same tester writes both arms, manual first, so the AI arm benefits from what the tester learned.
- **Fault realism:** seeded faults may not represent real defects; the fault author knows the code.
- **Tool and version:** results hold for one AI tool and version on one date.
- **AI-written implementation:** the SEFS code and acceptance tests were themselves drafted with AI, which may bias the kinds of defects present.
- **Open specification points:** Q1–Q9 are still placeholders; tests asserting a placeholder value may become wrong when the lecturer answers.

## 7. Write-up

The deliverables (Master's report, journal-style manuscript, 10-minute presentation) all draw on the same outputs:

| Section | Content | Source |
|---|---|---|
| Introduction | Why test cryptographic code; AI test generation; the RQ | |
| SEFS implementation | Parts 1–3, the format, interoperability results | `docs/`, `logs/interop_log.csv` |
| Method | Arms, budget, fault seeding and hiding, tools and versions, statistics | sections 3–4 |
| Results | Main table, statistics, area chart, per-fault discussion | `analysis/` |
| Discussion | Which faults one arm caught and the other missed, and why; AI rejection reasons; review vs writing time; real defects found | `results_by_fault.csv`, `ai_prompt_log.csv` |
| Threats to validity | Section 6 | |
| AI disclosure | As in the README | |

## 8. Checklist

- [ ] `sefs-v1.0` tagged; acceptance + format 18/18
- [x] Budget and AI tool agreed and written in section 3
- [ ] ≥ 20 faults written and applying (fault author)
- [ ] `tests/manual/` within budget; time and defect logs filled
- [ ] `tests/ai/run1/` within budget; prompt, time and defect logs filled
- [ ] Both suites pass on clean code
- [ ] `run_mutants.py` run for each arm; no `build_error` / `run_error` left
- [ ] Coverage measured for each arm
- [ ] `analyze.py` run; tables and chart in the report

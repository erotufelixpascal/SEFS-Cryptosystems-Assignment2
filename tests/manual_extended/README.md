# Manual arm, extended (no AI of any kind)

Extra manual tests written by the tester AFTER the main manual arm (`tests/manual/`, 120 min budget)
was finished. They are scored as a separate arm, "manual with more time", so the fixed-budget
comparison (manual vs ai/run1) stays fair.

Rules: same as `tests/manual/README.md`.

- Written by the tester (Daniel) only, with no AI tools (no Copilot, Claude, ChatGPT or AI autocomplete).
- Work from `docs/` and `tests/conftest.py` only; never open `mutants/` or `tests/acceptance/`.
- Do NOT copy or move tests from `tests/manual/`; that folder is frozen. Write new tests here.
- File names start with `test_` (e.g. `test_auth_more.py`), and so do test functions.
- Time each session and log it in `logs/time_log.csv` with arm `manual_extended`, e.g.
  `2026-11-26,Daniel Odong,manual_extended,more chunk tests,35`
- A test that fails on the unchanged code: log it in `logs/defect_log.csv` with arm `manual_extended`
  (`false_positive` = test wrong, `real_defect` = code wrong).
- Finish this BEFORE starting the AI arm, so AI suggestions cannot influence these tests.

Run:  python -m pytest tests\manual_extended -v

# Manual arm (no AI of any kind)

**Step-by-step guide:** [docs/MANUAL_TESTING_GUIDE.md](../../docs/MANUAL_TESTING_GUIDE.md)

Write the manual test suite here, by hand, within the agreed time budget.

- Turn off Copilot, Claude, ChatGPT and editor autocomplete suggestions before starting.
- Work only from `docs/` (the specification) and `tests/conftest.py`. Do not open `mutants/` or `tests/acceptance/`.
- Suggested files: `test_auth.py`, `test_roundtrip.py`, `test_chunks.py`, `test_tamper.py`.
- Log every working session in `logs/time_log.csv` with `arm` = `manual`.

Fixtures available (see `tests/conftest.py`): `sefs` (the module, in a fresh temp folder with a master key),
`user` (a registered `(username, password)`), `workdir` (the temp folder), `chunk_files` (lists chunk files).

```python
def test_example(sefs, user):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
```

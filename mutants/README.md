# Seeded faults (held-out evaluation set)

**Testers must not open this folder (apart from `examples/`) until scoring.** `mutants/*.toml` is git-ignored: the fault author keeps the faults private (e.g. with the supervisor) and copies them here only for scoring.

Each fault is one small, realistic bug in `src/sefs/`, described as find/replace edits in a TOML file named `Mnn_short_name.toml`. `tools/run_mutants.py` applies the edits to a **temporary copy** of the package, so `src/` is never changed and there is nothing to revert.

## Format

```toml
area = "chunk_boundaries"     # authentication | round_trip | chunk_boundaries | tamper
severity = "medium"           # low | medium | high
description = "One sentence: what the fault does"

[[edit]]
file = "src/sefs/fs.py"
find = "text that occurs exactly once in the file"
replace = "the faulty version"
```

- Add more `[[edit]]` blocks if the fault needs several changes (see `examples/X05_hmac_iv_only.toml`).
- For multi-line text use `"""…"""` or `'''…'''`. A newline directly after the opening quotes is ignored.
- If `find` occurs zero or several times, or the edit leaves a syntax error, the fault is reported as `build_error` and left out of the analysis. Fix it and rerun.

## Writing good faults

- Aim for **at least 5 faults per area** (20+ in total); the statistics have very little power with fewer.
- Make them realistic: off-by-one at 1,023/1,024/1,025, wrong padding byte, skipped HMAC check, IV reuse, wrong owner check, missing input validation, non-constant-time compare, old chunks not deleted, size field in the wrong byte order.
- Each fault must still let the code run. A fault that crashes on import tells you nothing.
- Write faults **without AI**, and don't reuse the ideas in `examples/`, since every tester has seen them.
- Check that each fault applies: `python tools\run_mutants.py --tests tests\acceptance` (any result other than `build_error` means the fault applies).

## examples/

Seven practice faults that show the format and let you check the scoring script. They are **not** part of the evaluation set; `run_mutants.py` only scores `*.toml` directly in `mutants/` unless you pass `--mutants-dir`.

| File | Area | What it breaks | Acceptance suite (measured 2026-11-18) |
|---|---|---|---|
| `X01_username_min_5` | authentication | `USER_MIN` 6 → 5 | missed |
| `X02_weak_pbkdf2` | authentication | PBKDF2 iterations 20000 → 1000 | missed |
| `X03_insert_drops_char` | round_trip | insert loses the character after the insertion point | detected |
| `X04_extra_chunk_at_boundary` | chunk_boundaries | a 1,024-byte file gets an extra empty chunk | detected |
| `X05_hmac_iv_only` | tamper | chunk HMAC covers only the IV | detected |
| `X06_read_skips_meta_digest` | tamper | `read_from_file` skips the Master File List digest check | missed |
| `X07_read_at_end_rejected` | round_trip | zero-length read at end of file fails | detected |

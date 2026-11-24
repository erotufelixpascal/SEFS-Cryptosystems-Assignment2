# SEFS: Secure Encrypted File System (Group 6, Python)

A pure-Python implementation of the SEFS assignment (Parts 1–3 plus interoperability), with the tooling for the Group 6 research extension:

> **Research question:** Does AI-assisted test generation find more implementation defects than manually designed tests under a fixed time budget?

The on-disk format is documented byte for byte in [docs/FILE_FORMAT.md](docs/FILE_FORMAT.md), so any group using the agreed format can read our files and we can read theirs.

| Part | Marks | Guide |
|---|---|---|
| 1. User authentication | 20 | [docs/PART1_USER_AUTHENTICATION.md](docs/PART1_USER_AUTHENTICATION.md) |
| 2. Simplified SEFS | 30 | [docs/PART2_SIMPLIFIED_SEFS.md](docs/PART2_SIMPLIFIED_SEFS.md) |
| 3. Full multi-chunk SEFS | 45 | [docs/PART3_FULL_SEFS.md](docs/PART3_FULL_SEFS.md) |
| 4. Cross-group interoperability | 5 | [docs/PART4_INTEROPERABILITY.md](docs/PART4_INTEROPERABILITY.md) |
| Extension: AI-assisted test generation | +25 | [docs/EXPERIMENT.md](docs/EXPERIMENT.md) |
| Writing the manual test suite | | [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) |
| On-disk format (reference) | | [docs/FILE_FORMAT.md](docs/FILE_FORMAT.md) |

---

## Quick start (Windows PowerShell)

Needs Python 3.11 or later (tested with 3.12.10).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .                      # optional: makes `sefs` importable from anywhere

python -m pytest tests\acceptance tests\format -v     # must show 18 passed
```

On Linux/macOS use `python3 -m venv .venv` and `source .venv/bin/activate`; everything else is the same.

### Use it from Python

All functions work on files in the **current working directory**.

```python
import sefs
sefs.generate_master_key()                                # master.key: 16-byte key + 16-byte IV
sefs.register_user("alice01", "Passw0rd#1", "passwd")      # 1
sefs.create_file("notes", "alice01", "Passw0rd#1")         # 1
sefs.write_to_file("notes", 0, b"hello world", "alice01", "Passw0rd#1")
sefs.read_from_file("notes", 6, 5, "alice01", "Passw0rd#1")   # b'world'
```

### Use it from the command line

```powershell
mkdir demo; cd demo
python -m sefs keygen
python -m sefs register alice01            # prompts for the password
python -m sefs encrypt report -u alice01   # 'report' is a plaintext file in this folder
python -m sefs read report 1019 10 -u alice01
python -m sefs health -u alice01
python -m sefs --help
```

`-p PASSWORD` skips the prompt; use it only with throwaway demo accounts.

---

## Layout

```
src/sefs/
  config.py       every format constant (open points marked TODO-confirm)
  crypto.py       AES-128-CTR, HMAC-SHA256, SHA-256, PBKDF2-HMAC-SHA1, secure random
  util.py         binary file I/O, atomic writes, hex, master key, paths
  auth.py         Part 1: register / delete / is_user_valid / match / change password
  chunk.py        one encrypted 1,024-byte chunk: write, verify-then-decrypt, delete
  meta.py         encrypted meta files and the Master File List
  fs.py           Parts 2-3: the nine file functions
  keygen.py       master key generator
  __main__.py     command-line interface
tests/
  conftest.py           fixtures: fresh temp folder + master key per test
  acceptance/           implementation acceptance checklist (15 tests)
  format/               known-answer tests of the on-disk format (3 tests)
  manual/               experiment arm A: hand-written tests (no AI)
  ai/run1/              experiment arm B: AI-proposed, human-validated tests
mutants/                seeded faults (hidden evaluation set) + examples/
tools/run_mutants.py    scores one suite against every seeded fault
tools/measure_coverage.py  line + branch coverage for one suite
tools/prepare_ai_run.py    isolated workspace + standard prompts for an AI-arm run
tools/log_prompt.py        appends a row to logs/ai_prompt_log.csv
analysis/analyze.py     results tables, McNemar test, bootstrap CIs, chart
logs/                   time, AI prompt/review, defect and interoperability logs
docs/                   the guides linked above
```

---

## Open specification points

The lecturer's `SEFS_Lecturer_Technical_Clarifications.md` is not in this folder yet. Until it is, the values below are placeholders, all in `src/sefs/config.py` and marked `TODO-confirm`. Change the constant, rerun the tests, and record the answer here.

| # | Question | Placeholder used now | Lecturer's answer |
|---|---|---|---|
| Q1 | Padding "ASCII character 0": `0x00` or `'0'` (0x30)? | `0x00` (`PAD_BYTE`) | Decided by the group 2026-11-21: keep the current value |
| Q2 | PBKDF2 output length; hex case | 20 bytes; lowercase written, either case read | Decided by the group 2026-11-24: keep the current value |
| Q3 | HMAC over ciphertext or plaintext; which key | HMAC-SHA256, chunk key, over IV ‖ ciphertext | Decided by the group 2026-11-21: keep the current value |
| Q4 | Meta encryption, field order, separators, line endings | AES-128-CTR(master key, master IV); see [FILE_FORMAT.md](docs/FILE_FORMAT.md) | Decided by the group 2026-11-21: keep the current value |
| Q5 | Chunk name length and character set | 32 lowercase hex chars; next-name field 32 bytes, `NULL` + zeros for the last chunk; size 4-byte big-endian | Decided by the group 2026-11-21: keep the current value |
| Q6 | Master File List encrypted? What is hashed? | Plaintext; `filename sha256hex`; digest of the stored (encrypted) meta bytes | Decided by the group 2026-11-21: keep the current value |
| Q7 | Integrity before decryption; `read_from_file` on failure | Yes, HMAC checked first; returns `None` | Decided by the group 2026-11-21: keep the current value |
| Q8 | Username/password bounds | Username `[A-Za-z0-9]{6,31}`; password `[A-Za-z0-9@#$%&*()-+=]{9,31}` | Decided by the group 2026-11-24: keep the current value |
| Q9 | Interoperability test files and exchange procedure | Not agreed yet; log in `logs/interop_log.csv` | |

Other assumptions: `write_to_file` **inserts** (later content shifts forward); `read_from_file` fails if `position + len` passes the end of the file; `encrypt_file` keeps the plaintext (`REMOVE_PLAINTEXT = False`); `master.key` is 16 key bytes followed by 16 IV bytes.

**Security note for the report:** encrypting every meta file with the same master key *and* IV in CTR mode reuses the keystream, so XORing two meta files leaks the XOR of their plaintexts. The code follows the specification as written; raise this with the lecturer and discuss it under limitations.

---

## Reproducing the experiment

Full protocol: [docs/EXPERIMENT.md](docs/EXPERIMENT.md). The commands, in order:

```powershell
python -m pytest tests\acceptance tests\format -q          # 0. implementation passes
git tag sefs-v1.0                                          #    freeze the code under test
python -m pytest tests\manual -q                           # 1. arm A passes on clean code
python -m pytest tests\ai\run1 -q                          # 2. arm B passes on clean code
python tools\run_mutants.py --tests tests\manual           # 3. score each arm
python tools\run_mutants.py --tests tests\ai\run1
python tools\measure_coverage.py --tests tests\manual      # 4. coverage
python tools\measure_coverage.py --tests tests\ai\run1
python analysis\analyze.py                                 # 5. tables, statistics, chart
```

Practice run with the example faults (before the real faults exist):

```powershell
python tools\run_mutants.py --tests tests\acceptance --mutants-dir mutants\examples
Remove-Item analysis\mutants_acceptance.csv
```

Measured on this machine on 2026-11-18: the acceptance suite detects 4 of the 7 example faults (X03, X04, X05, X07) and misses X01, X02 and X06.

---

## Data, keys and privacy

- No real user data is used. Every test makes its own synthetic users and file contents in a temporary folder.
- `master.key`, `passwd`, `masterlist`, `*.meta` and `chunks/` are git-ignored. Never commit keys or credentials.
- The seeded faults in `mutants/*.toml` are git-ignored, so testers cannot see them before scoring.

## AI usage disclosure

The Python implementation, acceptance and format tests, `tools/`, `analysis/analyze.py`, the example faults and these docs were drafted with Claude Code (Anthropic, Claude Opus 5.5) and reviewed by the group. The seeded faults (`mutants/*.toml`) and the manual arm (`tests/manual/`) must be written **without** AI. The AI arm (`tests/ai/`) is logged prompt by prompt in `logs/ai_prompt_log.csv`.

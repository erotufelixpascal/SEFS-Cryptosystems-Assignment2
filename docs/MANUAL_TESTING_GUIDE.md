# How to write the manual test suite (step by step)

**Arm:** `manual` (arm A, the baseline) · **Folder:** [`tests/manual/`](../tests/manual) · **Protocol:** [EXPERIMENT.md](EXPERIMENT.md), Step 2

This guide explains **how** to write and log the manual tests. It deliberately does **not** say **what** to test for SEFS. Deciding that is the work being measured, and any SEFS-specific test idea from an AI would contaminate the manual arm. The examples below use a made-up function, not SEFS.

> Disclosure for the report: this process guide was drafted with AI. It contains no SEFS test cases.

---

## Step 1: Ground rules (read once)

| Rule | Why |
|---|---|
| No AI of any kind while writing: Copilot, Claude, ChatGPT, AI autocomplete | This arm is the no-AI baseline |
| Work only from the docs listed in Step 4 and `tests/conftest.py` | The AI arm gets exactly the same material |
| Don't open `src/`, `tests/acceptance/`, `tests/format/`, `mutants/` or `tests/ai/` | You would be testing against the code or the faults instead of the specification |
| Use only the public `sefs.*` functions, not names starting with `_` | The AI arm is told the same, so both arms test the same interface |
| Stop when the agreed time budget is used up | Both arms get the same time |
| Log your time as you go | The logs are evidence; they can't be rebuilt afterwards |

The time budget counts **everything**: reading the spec, planning, writing, running and fixing tests.

---

## Step 2: Turn off AI tools

In VS Code:

1. **Extensions** (Ctrl+Shift+X): disable GitHub Copilot, Copilot Chat, Claude Code and any other AI extension (right-click → *Disable (Workspace)*).
2. **Settings** (Ctrl+,): search `inline suggest` and untick *Editor › Inline Suggest: Enabled*.
3. Close any AI chat windows and browser tabs.

Plain word completion (IntelliSense listing function names) is fine; it isn't AI.

---

## Step 3: Check your setup (≈ 2 minutes)

```powershell
cd "C:\Users\DELL USER\OneDrive\Desktop\UTAMU\Year 1 Sem 2\Cryptosystems\Assignment 2\SEF back up"
.venv\Scripts\Activate.ps1
python -m pytest tests\manual -v        # "collected 0 items" is expected at this point
```

Write down the time you start, then open `logs\time_log.csv` in VS Code, ready to add rows.

---

## Step 4: Read the specification and list its rules

Read these, in this order:

1. [PART1_USER_AUTHENTICATION.md](PART1_USER_AUTHENTICATION.md)
2. [PART2_SIMPLIFIED_SEFS.md](PART2_SIMPLIFIED_SEFS.md)
3. [PART3_FULL_SEFS.md](PART3_FULL_SEFS.md)
4. [FILE_FORMAT.md](FILE_FORMAT.md)
5. [`tests/conftest.py`](../tests/conftest.py) (the fixtures)

While reading, keep a **rule list** in `tests\manual\NOTES.md`: one line per testable statement in the spec, numbered and grouped by area. Testable statements usually contain words like *must*, *only*, *returns*, *rejects*, *exactly*, *at most* or *before*. For the made-up example:

```markdown
## authentication
R1  ages 0-120 are accepted
R2  anything else returns -1
R3  ...
```

The four areas used for scoring are `authentication`, `round_trip`, `chunk_boundaries` and `tamper`. Using the same grouping makes your results easy to compare by area later.

Skip rules for values marked **†** in FILE_FORMAT.md (open lecturer questions), unless you accept that those tests may change when the lecturer answers.

---

## Step 5: Turn each rule into test cases

For each rule, apply these standard test-design techniques:

| Technique | Question to ask | Made-up example: `check_age(n)` accepts 0–120 |
|---|---|---|
| **Equivalence classes** | Which groups of inputs should behave the same? Test one of each | a valid age (30), a negative age, an age that is too high |
| **Boundary values** | Where does behaviour change? Test on, just below and just above each edge | −1, 0, 1, 119, 120, 121 |
| **Invalid input** | Wrong type, empty, missing, too long, odd characters | `None`, `""`, `"abc"`, `3.5` |
| **Error paths** | What should fail, and how does it report failure? | returns −1 rather than crashing |
| **State and sequence** | Does the result depend on earlier calls? Test before/after | "after a reset, the old value no longer counts" |
| **Round trip** | If you store something and read it back, is it identical? | save then load returns the same bytes |
| **Fault injection** | If something on disk is damaged, is that detected? | change one byte of a stored file, then expect −1 |
| **Permissions** | Does the right person succeed and everyone else fail? | owner vs other user vs wrong password |

Write each case next to its rule in `NOTES.md` before coding it. This quick plan saves time and becomes evidence for the report.

---

## Step 6: Write the tests

### 6.1 Files

Create one file per area in `tests\manual\`. Names must start with `test_`:

```
tests\manual\test_auth.py
tests\manual\test_roundtrip.py
tests\manual\test_chunks.py
tests\manual\test_tamper.py
```

### 6.2 Shape of a test

Every test is a function whose name starts with `test_`. It takes fixtures as arguments and follows **Arrange → Act → Assert**:

```python
# R2: anything outside 0-120 returns -1
def test_age_above_maximum_rejected(sefs, user):
    u, p = user                      # Arrange: get what you need
    result = ...                     # Act: call ONE public sefs function
    assert result == -1              # Assert: what the spec says must happen
```

- **One behaviour per test**, so a failure tells you exactly what broke.
- **A descriptive name**: `test_<what>_<condition>_<expected>`.
- **A comment naming the rule** (`# R2: ...`) so a reviewer can check the test against the spec.
- **Assert exact values** (`== 1`, `== -1`, `== b"..."`, `is None`), not just "truthy".

### 6.3 The fixtures

| Fixture | What it gives you |
|---|---|
| `sefs` | The SEFS module. The test runs in a fresh, empty temp folder that already has a `master.key` |
| `user` | `(username, password)` of a user already registered in `passwd` |
| `workdir` | That temp folder as a `pathlib.Path` |
| `chunk_files` | A function: `chunk_files()` returns the list of chunk files on disk |

Every test starts from an empty folder, so tests never depend on each other. You can run them in any order.

### 6.4 Return values (from the spec)

| Function | Success | Failure |
|---|---|---|
| Most functions | `1` | `-1` |
| `read_from_file` | `bytes` | `None` |
| `file_size` | the size (≥ 0) | `-1` |

### 6.5 Useful Python techniques

**Create a plaintext file on disk** (for functions that read one):

```python
from pathlib import Path
Path("myfile").write_bytes(b"some content")
```

**Run one test for many inputs** with `parametrize`:

```python
import pytest

@pytest.mark.parametrize("age, expected", [(-1, -1), (0, 1), (120, 1), (121, -1)])
def test_age_boundaries(age, expected):
    assert check_age(age) == expected
```

Each parameter set is reported as its own test, which suits boundary testing.

**Damage a file on disk** (fault injection):

```python
target = workdir / "some_file"
data = bytearray(target.read_bytes())
data[10] ^= 0x01                 # flip one bit
target.write_bytes(data)
```

`del`-ing a file (`target.unlink()`), swapping two files' contents, or appending bytes are other kinds of damage.

**Make large or binary content:**

```python
content = b"A" * 5000            # repeated bytes
content = bytes(range(256)) * 4  # every byte value, including 0x00 and 0x1A
```

Prefer fixed content over `os.urandom` so a failure can be reproduced exactly.

---

## Step 7: Run tests as you go

```powershell
python -m pytest tests\manual -v                         # everything
python -m pytest tests\manual\test_auth.py -v            # one file
python -m pytest tests\manual -v -k boundaries           # tests whose name contains "boundaries"
python -m pytest tests\manual -x                         # stop at the first failure
python -m pytest tests\manual -v --tb=short              # shorter error output
```

Run after every few tests. A test you never ran may be wrong.

---

## Step 8: When a test fails, decide who is wrong

Re-read the rule in the spec, then:

| Situation | Classification | What to do |
|---|---|---|
| The test matches the spec, the code doesn't | `real_defect` | **Keep the test unchanged.** Don't fix `src/`. Log it |
| The test misread the spec, or has a bug | `false_positive` | Log it, **then** fix or delete the test |
| The spec is genuinely unclear | — | Note it in `NOTES.md`, ask the lecturer, and don't assert either way |

Log each one in `logs\defect_log.csv` straight away (one line, no spaces after commas):

```
D-001,2026-11-20,Your Name,manual,test_auth.py::test_name,function_called,What happened in one sentence,false_positive,Fixed the expected value
```

Use the next free `D-` number. These rows give the *false-positive test failures* and *valid defects discovered* figures the brief asks for.

---

## Step 9: Log your time

At the end of each working session, add one row to `logs\time_log.csv`:

```
2026-11-20,Your Name,manual,reading spec + rule list,40
2026-11-20,Your Name,manual,auth tests,55
2026-11-21,Your Name,manual,tamper tests + fixing false positives,50
```

`arm` is always `manual`. When the total reaches the budget, **stop**, even mid-idea, and note unfinished ideas in `NOTES.md` for the discussion section.

---

## Step 10: Finish and hand over

1. Run the full suite on the unchanged code:
   ```powershell
   python -m pytest tests\manual -v
   ```
   Everything should pass, except tests that found a `real_defect` you logged. For scoring, the suite must pass on clean code, so mark those tests:
   ```python
   @pytest.mark.xfail(reason="D-003 real defect, see defect_log.csv")
   ```
   Leave out `strict=True`: with it, a seeded fault that happens to make this test pass would be counted as "detected" for the wrong reason. Mark real defects the same way in the AI arm.
2. Count your tests: `python -m pytest tests\manual --collect-only -q`
3. Commit: `git add tests/manual logs; git commit -m "Manual arm complete"`
4. Don't change `tests\manual\` after this point.
5. Only now start the AI arm ([EXPERIMENT.md](EXPERIMENT.md), Step 3), then score both suites:
   ```powershell
   python tools\run_mutants.py --tests tests\manual
   python tools\measure_coverage.py --tests tests\manual --html
   ```

---

## Common mistakes

| Mistake | Effect | Avoid by |
|---|---|---|
| Asserting something the spec doesn't say | False positives | Every test cites a rule number |
| Several behaviours in one test | Unclear which one failed | One Act and one Assert idea per test |
| Writing many tests before running any | A pile of broken tests at the end | Run after every few tests |
| Using random data | Failures you can't reproduce | Fixed byte patterns |
| Fixing `src/` when a test finds a bug | Arms scored against different code | Log it; leave `src/` alone |
| Calling `_private` functions | Not comparable with the AI arm | Public `sefs.*` functions only |
| Writing time logs afterwards | Weak evidence | Log at the end of every session |

## Checklist

- [ ] AI tools off; start time noted
- [ ] Rule list in `tests\manual\NOTES.md`, grouped by the four areas
- [ ] Tests in `tests\manual\test_*.py`, each citing its rule
- [ ] Every failure classified and logged in `defect_log.csv`
- [ ] Time logged in `time_log.csv`; stopped at the budget
- [ ] Suite passes on clean code (real defects marked `xfail`)
- [ ] Committed; no changes afterwards

"""Prepare an isolated workspace for one AI-assisted test-generation run.

    python tools/prepare_ai_run.py --run run1

Creates, OUTSIDE the project folder (default: ../SEF_ai_workspace/<run>/):

    CONTEXT.md   the specification the AI may see: docs/PART1-3, docs/FILE_FORMAT.md, tests/conftest.py
    conftest.py  copy of tests/conftest.py (fixtures the tests must use)
    CLAUDE.md    rules for an AI coding assistant opened in that folder
    PROMPTS.md   the standard prompts for this run
    proposed/    where the AI writes its proposed test files

and makes sure tests/ai/<run>/ exists in the project. The workspace holds no
source code, no acceptance tests, no manual tests and no seeded faults, so
the AI cannot see anything the manual arm did not have.
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ["docs/PART1_USER_AUTHENTICATION.md", "docs/PART2_SIMPLIFIED_SEFS.md",
        "docs/PART3_FULL_SEFS.md", "docs/FILE_FORMAT.md"]

CLAUDE_MD = """# Rules for this session (Group 6 AI arm, {run})

You are helping write pytest tests for SEFS, a secure encrypted file system, as one arm of a
controlled experiment. Follow these rules exactly:

- Use ONLY the files in this folder: CONTEXT.md (the specification) and conftest.py (fixtures).
  Do not open, list or search any file outside this folder, even if asked to.
- You cannot see or run the implementation. Write tests from the specification alone.
- Every test uses the fixtures in conftest.py (`sefs`, `user`, `workdir`, `chunk_files`) and calls
  the functions through the `sefs` fixture, e.g. `sefs.create_file("notes", u, p)`.
- Write proposed tests to `proposed/test_<area>_<prompt id>.py`, one file per prompt.
- Put a comment above each test saying which rule in CONTEXT.md it checks.
- Never invent behaviour the specification does not state; if something is unclear, say so
  instead of guessing.
- Do not write tests that depend on placeholder values marked with a dagger (†) in
  FILE_FORMAT.md unless the prompt asks for format tests.
"""

PROMPTS_MD = """# Standard prompts ({run})

Use these prompts in order, in ONE fresh session. Paste them as written so every run is
comparable; if you change one, log the exact text you sent. After each prompt, review every
proposed test (section "Review" below) and log the prompt with tools/log_prompt.py.

| id | area | prompt |
|---|---|---|
| 1 | authentication | Read CONTEXT.md and conftest.py. Propose pytest tests for Part 1 (user authentication): register_user, delete_user, is_user_valid, match_user and change_user_password, including input-validation boundaries. Write them to proposed/test_authentication_<id>.py. |
| 2 | round_trip | Propose pytest tests for encryption round trips: create_file, encrypt_file, decrypt_file, read_from_file, write_to_file and file_size must return exactly the data that was stored, for empty, small and binary contents. Write them to proposed/test_round_trip_<id>.py. |
| 3 | chunk_boundaries | Propose pytest tests for chunk boundaries: file sizes and read/write positions around 0, 1023, 1024, 1025, 2047, 2048 and 2049 bytes, the chunk-count rule, appends to partial chunks and inserts that spill into a new chunk. Write them to proposed/test_chunk_boundaries_<id>.py. |
| 4 | tamper | Propose pytest tests for tamper handling: modified, missing, swapped and extra chunk files, edited meta files, edited Master File List, and wrong owners or passwords, for file_integrity_check, system_health_check and the read/write functions. Write them to proposed/test_tamper_<id>.py. |
| 5 | any | Review the tests proposed so far against CONTEXT.md. List any rule in the specification that no test checks yet, then propose tests for those. Write them to proposed/test_gaps_<id>.py. |

Replace `<id>` with the prompt id that tools/log_prompt.py will assign (P-001, P-002, ...).

## Review (for every proposed test)

1. Copy the file into the project's `tests/ai/{run}/` and run it:
   `python -m pytest tests\\ai\\{run}\\<file> -v`
2. For each test decide:
   - **accepted**: correct per the specification, kept unchanged;
   - **edited**: right idea, but you had to fix it (record why);
   - **rejected**: wrong, duplicate or untestable (record why) - delete it.
3. A test that fails on the unchanged code: check the specification. If the test is right, it found
   a real defect - keep it and log it in logs/defect_log.csv as `real_defect`. If the test is
   wrong, it is a `false_positive` - log it, then fix or reject it.
4. Tag every kept test with its prompt: `# source: P-001` or `# source: P-001 (edited)`.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="run1", help="run name, e.g. run1, run2")
    ap.add_argument("--out", type=Path, help="workspace folder (default ../SEF_ai_workspace/<run>)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing workspace")
    a = ap.parse_args()

    ws = (a.out or ROOT.parent / "SEF_ai_workspace" / a.run).resolve()
    if ws.is_relative_to(ROOT):
        print("the workspace must be outside the project folder, or the AI could read mutants/ and tests/",
              file=sys.stderr)
        return 2
    if ws.exists() and any(ws.iterdir()) and not a.force:
        print(f"{ws} already exists and is not empty (use --force to rebuild it)", file=sys.stderr)
        return 1
    (ws / "proposed").mkdir(parents=True, exist_ok=True)

    parts = ["# SEFS specification (context for test generation)\n",
             "Everything the tests may rely on is in this file and in conftest.py.\n"]
    for rel in SPEC:
        parts.append(f"\n\n---\n\n<!-- {rel} -->\n\n" + (ROOT / rel).read_text(encoding="utf-8"))
    conftest = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    parts.append("\n\n---\n\n<!-- tests/conftest.py -->\n\n```python\n" + conftest + "```\n")
    (ws / "CONTEXT.md").write_text("".join(parts), encoding="utf-8")
    shutil.copyfile(ROOT / "tests" / "conftest.py", ws / "conftest.py")
    (ws / "CLAUDE.md").write_text(CLAUDE_MD.format(run=a.run), encoding="utf-8")
    (ws / "PROMPTS.md").write_text(PROMPTS_MD.format(run=a.run), encoding="utf-8")

    arm = ROOT / "tests" / "ai" / a.run
    arm.mkdir(parents=True, exist_ok=True)
    print(f"workspace ready: {ws}")
    print(f"accepted tests go in: {arm.relative_to(ROOT)}")
    print("next: open a NEW AI session in the workspace folder and follow PROMPTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

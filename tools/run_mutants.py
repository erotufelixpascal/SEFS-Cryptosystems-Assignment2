"""Score one test suite against every seeded fault (mutant).

For each ``<id>.toml`` in the mutants folder: copy src/sefs to a temporary
folder, apply the fault's find/replace edits, run the suite against that
copy, and record whether any test failed (``detected``) or all passed
(``missed``). The real src/ is never modified.

    python tools/run_mutants.py --tests tests/manual
    python tools/run_mutants.py --tests tests/ai/run1
    python tools/run_mutants.py --tests tests/acceptance --mutants-dir mutants/examples

Writes analysis/mutants_<arm>.csv, where <arm> is the suite path below tests/
with "/" replaced by "_" (manual, ai_run1, ...).

Mutant file format (TOML):

    area = "tamper"                # authentication | round_trip | chunk_boundaries | tamper
    severity = "high"              # low | medium | high
    description = "One sentence describing the fault"

    [[edit]]
    file = "src/sefs/chunk.py"
    find = '''text that must occur exactly once'''
    replace = '''its replacement'''
"""

import argparse
import csv
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AREAS = {"authentication", "round_trip", "chunk_boundaries", "tamper"}


def arm_name(tests: Path) -> str:
    rel = tests.resolve().relative_to((ROOT / "tests").resolve())
    return rel.as_posix()


def run_suite(tests: Path, sefs_src: Path | None, timeout: int) -> tuple[str, str]:
    """Returns (result, detail). result is passed / failed / run_error / timeout."""
    env = dict(os.environ)
    env.pop("SEFS_SRC", None)
    if sefs_src is not None:
        env["SEFS_SRC"] = str(sefs_src)
    cmd = [sys.executable, "-m", "pytest", str(tests), "-q", "-x", "-rf", "--no-header", "-p", "no:randomly"]
    try:
        r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", f"suite exceeded {timeout}s"
    out = r.stdout + r.stderr
    if r.returncode == 0:
        return "passed", "all tests passed"
    if r.returncode == 1:
        m = re.search(r"^FAILED (\S+)", out, re.M)
        return "failed", m.group(1) if m else "a test failed"
    if r.returncode == 5:
        return "run_error", "no tests collected"
    last = [l for l in out.strip().splitlines() if l.strip()][-1:] or ["pytest error"]
    return "run_error", f"pytest exit {r.returncode}: {last[0][:200]}"


def apply_mutant(spec: dict, dest: Path) -> str | None:
    """Apply every edit to the package copy under dest. Returns an error message or None."""
    edits = spec.get("edit") or []
    if not edits:
        return "no [[edit]] entries"
    for e in edits:
        rel = Path(e.get("file", ""))
        parts = rel.parts
        if len(parts) < 3 or parts[0] != "src" or parts[1] != "sefs":
            return f"file must be under src/sefs/: {rel}"
        target = dest.joinpath(*parts[1:])
        if not target.exists():
            return f"no such file: {rel}"
        text = target.read_text(encoding="utf-8").replace("\r\n", "\n")
        find = e.get("find", "").replace("\r\n", "\n")
        count = text.count(find) if find else 0
        if count != 1:
            return f"'find' occurs {count} times in {rel} (must be exactly once)"
        text = text.replace(find, e.get("replace", "").replace("\r\n", "\n"))
        target.write_text(text, encoding="utf-8", newline="\n")
        try:
            py_compile.compile(str(target), doraise=True)
        except py_compile.PyCompileError as exc:
            return f"syntax error after edit: {exc.msg.strip().splitlines()[-1]}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True, type=Path, help="test folder, e.g. tests/manual")
    ap.add_argument("--mutants-dir", type=Path, default=ROOT / "mutants")
    ap.add_argument("--timeout", type=int, default=600, help="seconds per suite run")
    ap.add_argument("--out", type=Path, help="CSV path (default analysis/mutants_<arm>.csv)")
    a = ap.parse_args()

    tests = a.tests if a.tests.is_absolute() else (ROOT / a.tests)
    if not tests.is_dir():
        print(f"no such test folder: {tests}", file=sys.stderr)
        return 2
    arm = arm_name(tests)
    out = a.out or ROOT / "analysis" / f"mutants_{arm.replace('/', '_')}.csv"
    mutants = sorted(a.mutants_dir.glob("*.toml"))
    if not mutants:
        print(f"no *.toml faults in {a.mutants_dir}\n"
              "The real seeded faults have not been written yet. The fault author writes them by hand\n"
              "(no AI), as described in mutants/README.md. To practise with the example faults instead:\n"
              "  python tools/run_mutants.py --tests tests/acceptance --mutants-dir mutants/examples",
              file=sys.stderr)
        return 2

    print(f"[{arm}] baseline: running the suite on the unmodified code ...")
    base, detail = run_suite(tests, None, a.timeout)
    if base != "passed":
        hint = ("\nThis arm has no tests yet. Write them first (see the README.md in that folder)."
                if detail == "no tests collected" else "")
        print(f"[{arm}] the suite must pass on clean code before scoring ({base}: {detail}){hint}",
              file=sys.stderr)
        return 1

    rows = []
    for path in mutants:
        mid = path.stem
        t0 = time.perf_counter()
        try:
            spec = tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            spec, err = {}, f"bad TOML: {exc}"
        else:
            err = None
        area = spec.get("area", "")
        if err is None and area not in AREAS:
            err = f"area must be one of {sorted(AREAS)}"
        if err is None:
            with tempfile.TemporaryDirectory(prefix="sefs_mut_") as tmp:
                pkg = Path(tmp) / "sefs"
                shutil.copytree(ROOT / "src" / "sefs", pkg,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                err = apply_mutant(spec, Path(tmp))
                if err is None:
                    res, detail = run_suite(tests, Path(tmp), a.timeout)
        if err is not None:
            result, detail = "build_error", err
        else:
            result = {"failed": "detected", "timeout": "detected", "passed": "missed"}.get(res, "run_error")
            if res == "timeout":
                detail = "timeout (counted as detected)"
        secs = time.perf_counter() - t0
        rows.append({
            "arm": arm, "id": mid, "area": area, "severity": spec.get("severity", ""),
            "description": spec.get("description", ""), "result": result, "detail": detail,
            "seconds": f"{secs:.1f}",
        })
        print(f"[{arm}] {mid:<32} {result:<12} {detail}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    scored = [r for r in rows if r["result"] in ("detected", "missed")]
    hit = sum(r["result"] == "detected" for r in scored)
    print(f"[{arm}] {hit}/{len(scored)} faults detected; results in {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

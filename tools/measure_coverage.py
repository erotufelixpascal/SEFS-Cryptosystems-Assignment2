"""Measure line and branch coverage of src/sefs for one test suite.

    python tools/measure_coverage.py --tests tests/manual
    python tools/measure_coverage.py --tests tests/ai/run1 --html

Writes analysis/coverage_<arm>.json (read by analysis/analyze.py) and, with
--html, an HTML report in analysis/htmlcov_<arm>/.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True, type=Path)
    ap.add_argument("--html", action="store_true")
    a = ap.parse_args()

    tests = (a.tests if a.tests.is_absolute() else ROOT / a.tests).resolve()
    arm = tests.relative_to((ROOT / "tests").resolve()).as_posix().replace("/", "_")
    data_file = ROOT / f".coverage.{arm}"
    env = dict(os.environ, COVERAGE_FILE=str(data_file))
    env.pop("SEFS_SRC", None)
    src = str(ROOT / "src" / "sefs")

    # The CLI (__main__.py) is demo glue around the library, so it is left out of the measure.
    r = subprocess.run([sys.executable, "-m", "coverage", "run", "--branch", f"--source={src}",
                        "--omit=*/__main__.py", "-m", "pytest", str(tests), "-q"], cwd=ROOT, env=env)
    if r.returncode not in (0, 1):
        print("pytest did not run; no coverage written", file=sys.stderr)
        return r.returncode
    if r.returncode == 1:
        print("warning: some tests failed; coverage is still recorded", file=sys.stderr)

    out = ROOT / "analysis" / f"coverage_{arm}.json"
    out.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-m", "coverage", "json", "-o", str(out), "-q"], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, "-m", "coverage", "report"], cwd=ROOT, env=env)
    if a.html:
        subprocess.run([sys.executable, "-m", "coverage", "html", "-d", str(ROOT / "analysis" / f"htmlcov_{arm}"),
                        "-q"], cwd=ROOT, env=env)
    print(f"coverage written to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

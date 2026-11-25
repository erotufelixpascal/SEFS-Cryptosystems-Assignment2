"""Turn the experiment's measurements into tables, statistics and a chart.

    python analysis/analyze.py
    python analysis/analyze.py --arms manual ai/run1 --seed 2026

Inputs (all optional except the mutant results):
  analysis/mutants_<arm>.csv     from tools/run_mutants.py   (one per arm)
  analysis/coverage_<arm>.json   from tools/measure_coverage.py
  logs/time_log.csv              date,student,arm,activity,minutes
  logs/defect_log.csv            defect_id,date,student,arm,test,function,description,classification,resolution
  logs/ai_prompt_log.csv         prompt_id,timestamp,run,tool_version,area,prompt_text,tests_proposed,
                                 accepted,edited,rejected,rejection_reason,review_minutes

Outputs in analysis/:
  results_table.csv      one row per arm: mutation score, coverage, real defects, false positives, time
  statistics.csv         manual vs each AI arm: McNemar exact test, 95% bootstrap CIs
  results_by_area.csv    detection rate per fault area per arm
  results_by_fault.csv   one row per fault with each arm's result and detail
  results.md             all of the above as Markdown tables
  fig_detection_by_area.png  (if matplotlib is installed)

Only faults scored detected/missed in EVERY arm are counted, so all arms
share one denominator. The 'acceptance' arm is excluded unless named.
"""

import argparse
import csv
import json
import math
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "analysis"
LOGS = ROOT / "logs"
AREAS = ["authentication", "round_trip", "chunk_boundaries", "tamper"]


def slug(arm: str) -> str:
    return arm.replace("/", "_")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def num(s, default=0.0) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def count_tests(arm: str) -> int | None:
    folder = ROOT / "tests" / arm
    if not folder.is_dir():
        return None
    r = subprocess.run([sys.executable, "-m", "pytest", str(folder), "--collect-only", "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return sum(1 for line in r.stdout.splitlines() if "::" in line)


# ---------------- statistics ----------------

def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value. b = caught only by arm A, c = caught only by arm B."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_ci(pairs: list[tuple[int, int]], reps: int, rng: random.Random) -> tuple[float, float]:
    """95% percentile CI for mean(b) - mean(a) over paired 0/1 outcomes, resampling faults."""
    n = len(pairs)
    if n == 0:
        return (math.nan, math.nan)
    diffs = []
    for _ in range(reps):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(sum(b - a for a, b in s) / n)
    diffs.sort()
    return diffs[int(0.025 * reps)], diffs[min(reps - 1, int(0.975 * reps))]


def wilson(k: int, n: int) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (math.nan, math.nan)
    z = 1.96
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def pct(x: float) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def md_table(rows: list[dict]) -> str:
    if not rows:
        return "_no data_\n"
    cols = list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(lines) + "\n"


# ---------------- main ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="*", help="arms to compare, e.g. manual ai/run1 (default: all found)")
    ap.add_argument("--baseline", default="manual")
    ap.add_argument("--reps", type=int, default=10000, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()

    found = {}
    for path in sorted(HERE.glob("mutants_*.csv")):
        rows = read_csv(path)
        if rows:
            found[rows[0].get("arm") or path.stem[len("mutants_"):]] = rows
    arms = a.arms or [arm for arm in found if arm != "acceptance"]
    missing = [arm for arm in arms if arm not in found]
    if missing or not arms:
        print(f"no mutant results for {missing or 'any arm'}; run tools/run_mutants.py first", file=sys.stderr)
        return 1
    # baseline first, then the others in name order
    arms = sorted(arms, key=lambda x: (x != a.baseline, x))

    # Faults scored in every arm
    results = {arm: {r["id"]: r for r in found[arm]} for arm in arms}
    ids = sorted(set.intersection(*(set(results[arm]) for arm in arms)))
    scored = [i for i in ids if all(results[arm][i]["result"] in ("detected", "missed") for arm in arms)]
    excluded = sorted(set().union(*(set(results[arm]) for arm in arms)) - set(scored))
    caught = {arm: {i: int(results[arm][i]["result"] == "detected") for i in scored} for arm in arms}
    meta = {i: results[arms[0]][i] for i in scored}

    time_rows = read_csv(LOGS / "time_log.csv")
    defect_rows = read_csv(LOGS / "defect_log.csv")
    prompt_rows = read_csv(LOGS / "ai_prompt_log.csv")

    table = []
    for arm in arms:
        k, n = sum(caught[arm].values()), len(scored)
        lo, hi = wilson(k, n)
        cov_path = HERE / f"coverage_{slug(arm)}.json"
        line_cov = branch_cov = None
        if cov_path.exists():
            t = json.loads(cov_path.read_text(encoding="utf-8"))["totals"]
            line_cov = t["covered_lines"] / t["num_statements"] if t.get("num_statements") else None
            branch_cov = t["covered_branches"] / t["num_branches"] if t.get("num_branches") else None
        minutes = sum(num(r.get("minutes")) for r in time_rows if r.get("arm") == arm)
        real = sum(1 for r in defect_rows if r.get("arm") == arm and r.get("classification") == "real_defect")
        fp = sum(1 for r in defect_rows if r.get("arm") == arm and r.get("classification") == "false_positive")
        prompts = [r for r in prompt_rows if r.get("run") == arm]
        ntests = count_tests(arm)
        table.append({
            "arm": arm,
            "tests": ntests if ntests is not None else "n/a",
            "faults_detected": f"{k}/{n}",
            "mutation_score": pct(k / n if n else math.nan),
            "score_95ci": f"{pct(lo)}-{pct(hi)}",
            "line_coverage": pct(line_cov) if line_cov is not None else "n/a",
            "branch_coverage": pct(branch_cov) if branch_cov is not None else "n/a",
            "real_defects": real,
            "false_positives": fp,
            "minutes": f"{minutes:g}",
            "faults_per_hour": f"{k / (minutes / 60):.2f}" if minutes else "n/a",
            "valid_findings_per_hour": f"{(k + real) / (minutes / 60):.2f}" if minutes else "n/a",
            "ai_prompts": len(prompts) if prompts else "",
            "ai_tests_proposed": int(sum(num(r.get("tests_proposed")) for r in prompts)) if prompts else "",
            "ai_accepted": int(sum(num(r.get("accepted")) for r in prompts)) if prompts else "",
            "ai_edited": int(sum(num(r.get("edited")) for r in prompts)) if prompts else "",
            "ai_rejected": int(sum(num(r.get("rejected")) for r in prompts)) if prompts else "",
            "ai_review_minutes": f"{sum(num(r.get('review_minutes')) for r in prompts):g}" if prompts else "",
        })

    rng = random.Random(a.seed)
    stats = []
    base = arms[0]
    for arm in arms[1:]:
        b = sum(1 for i in scored if caught[base][i] and not caught[arm][i])
        c = sum(1 for i in scored if caught[arm][i] and not caught[base][i])
        lo, hi = bootstrap_ci([(caught[base][i], caught[arm][i]) for i in scored], a.reps, rng)
        diff = (sum(caught[arm].values()) - sum(caught[base].values())) / len(scored) if scored else math.nan
        stats.append({
            "comparison": f"{arm} vs {base}",
            "faults": len(scored),
            # Fixed column names, so rows for several comparisons share one CSV header.
            "only_baseline": b,
            "only_other_arm": c,
            "both": sum(1 for i in scored if caught[base][i] and caught[arm][i]),
            "neither": sum(1 for i in scored if not caught[base][i] and not caught[arm][i]),
            "score_difference": f"{100 * diff:+.1f} pts",
            "diff_95ci_bootstrap": f"{100 * lo:+.1f} to {100 * hi:+.1f} pts",
            "mcnemar_exact_p": f"{mcnemar_exact(b, c):.4f}",
        })

    by_area = []
    for area in AREAS + sorted({m["area"] for m in meta.values()} - set(AREAS)):
        in_area = [i for i in scored if meta[i]["area"] == area]
        row = {"area": area, "faults": len(in_area)}
        for arm in arms:
            k = sum(caught[arm][i] for i in in_area)
            row[arm] = pct(k / len(in_area)) if in_area else "n/a"
        by_area.append(row)

    by_fault = []
    for i in scored:
        row = {"id": i, "area": meta[i]["area"], "severity": meta[i].get("severity", ""),
               "description": meta[i].get("description", "")}
        for arm in arms:
            row[arm] = results[arm][i]["result"]
            row[f"{arm}_detail"] = results[arm][i]["detail"]
        by_fault.append(row)

    write_csv(HERE / "results_table.csv", table)
    write_csv(HERE / "statistics.csv", stats)
    write_csv(HERE / "results_by_area.csv", by_area)
    write_csv(HERE / "results_by_fault.csv", by_fault)

    md = ["# Experiment results\n",
          f"Arms: {', '.join(arms)}. Faults scored in every arm: {len(scored)}."
          + (f" Excluded (build/run error or not scored in every arm): {', '.join(excluded)}." if excluded else "")
          + "\n",
          "## Per arm\n", md_table(table),
          f"## {base} vs each other arm\n", md_table(stats),
          "McNemar's exact test uses only the faults one arm caught and the other missed. "
          f"Bootstrap: {a.reps} paired resamples of faults, seed {a.seed}.\n",
          "## Detection by area\n", md_table(by_area),
          "## Per fault\n", md_table([{k: v for k, v in r.items() if not k.endswith('_detail')} for r in by_fault])]
    (HERE / "results.md").write_text("\n".join(md), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        areas = [r["area"] for r in by_area if r["faults"]]
        width = 0.8 / len(arms)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for j, arm in enumerate(arms):
            vals = []
            for area in areas:
                ia = [i for i in scored if meta[i]["area"] == area]
                vals.append(100 * sum(caught[arm][i] for i in ia) / len(ia))
            ax.bar([x + j * width for x in range(len(areas))], vals, width, label=arm)
        ax.set_xticks([x + width * (len(arms) - 1) / 2 for x in range(len(areas))], areas)
        ax.set_ylabel("Seeded faults detected (%)")
        ax.set_ylim(0, 105)
        ax.set_title("Fault detection by area")
        ax.legend()
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(HERE / "fig_detection_by_area.png", dpi=200)
    except ImportError:
        print("matplotlib not installed; chart skipped")

    print((HERE / "results.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

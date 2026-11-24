"""Append one row to logs/ai_prompt_log.csv, with the next prompt id and the current time.

Before sending a prompt, reserve its id:

    python tools/log_prompt.py next

After reviewing the tests it produced, log it:

    python tools/log_prompt.py add --run ai/run1 --area chunk_boundaries --prompt-number 3 ^
        --proposed 8 --accepted 5 --edited 2 --rejected 1 ^
        --reason "asserted a placeholder padding byte" --minutes 14

--prompt-number N takes prompt N's text from the standard prompts (PROMPTS.md);
use --prompt "exact text" or --prompt-file file.txt if you sent something else.
The tool and version default to SEFS_AI_TOOL, or pass --tool "Claude Opus 5.5".
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "ai_prompt_log.csv"
FIELDS = ["prompt_id", "timestamp", "run", "tool_version", "area", "prompt_text", "tests_proposed",
          "accepted", "edited", "rejected", "rejection_reason", "review_minutes"]
AREAS = ["authentication", "round_trip", "chunk_boundaries", "tamper", "any"]


def next_id() -> str:
    n = 0
    if LOG.exists():
        with open(LOG, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                m = re.fullmatch(r"P-(\d+)", (row.get("prompt_id") or "").strip())
                if m:
                    n = max(n, int(m.group(1)))
    return f"P-{n + 1:03d}"


def standard_prompt(number: int) -> str | None:
    sys.path.insert(0, str(ROOT / "tools"))
    from prepare_ai_run import PROMPTS_MD
    for line in PROMPTS_MD.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] == str(number):
            return cells[2]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next", help="print the next prompt id")
    add = sub.add_parser("add", help="append one logged prompt")
    add.add_argument("--run", required=True, help="e.g. ai/run1")
    add.add_argument("--area", required=True, choices=AREAS)
    g = add.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt", help="the exact prompt text sent")
    g.add_argument("--prompt-file", type=Path)
    g.add_argument("--prompt-number", type=int, help="standard prompt number from PROMPTS.md")
    add.add_argument("--tool", default=os.environ.get("SEFS_AI_TOOL", ""), help="AI tool and version")
    for name in ("proposed", "accepted", "edited", "rejected"):
        add.add_argument(f"--{name}", type=int, required=True)
    add.add_argument("--reason", default="", help="why tests were rejected or edited")
    add.add_argument("--minutes", type=float, required=True, help="minutes spent reviewing")
    add.add_argument("--id", help="prompt id (default: the next free one)")
    a = ap.parse_args()

    if a.cmd == "next":
        print(next_id())
        return 0

    if not a.run.startswith("ai/"):
        print("--run must look like ai/run1", file=sys.stderr)
        return 2
    if not a.tool:
        print("give --tool (e.g. \"Claude Opus 5.5\") or set SEFS_AI_TOOL", file=sys.stderr)
        return 2
    if a.accepted + a.edited + a.rejected != a.proposed:
        print(f"accepted + edited + rejected ({a.accepted + a.edited + a.rejected}) "
              f"must equal proposed ({a.proposed})", file=sys.stderr)
        return 2
    if a.prompt_number is not None:
        text = standard_prompt(a.prompt_number)
        if text is None:
            print(f"no standard prompt number {a.prompt_number}", file=sys.stderr)
            return 2
    else:
        text = a.prompt if a.prompt is not None else a.prompt_file.read_text(encoding="utf-8")

    row = {
        "prompt_id": a.id or next_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "run": a.run, "tool_version": a.tool, "area": a.area,
        "prompt_text": " ".join(text.split()),
        "tests_proposed": a.proposed, "accepted": a.accepted, "edited": a.edited, "rejected": a.rejected,
        "rejection_reason": a.reason, "review_minutes": f"{a.minutes:g}",
    }
    new = not LOG.exists() or LOG.stat().st_size == 0
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"logged {row['prompt_id']} ({a.run}, {a.area}): "
          f"{a.proposed} proposed, {a.accepted} accepted, {a.edited} edited, {a.rejected} rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main())

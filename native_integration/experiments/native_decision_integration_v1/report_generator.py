"""Frozen application fixture: deliberately excludes negative transactions."""

import csv
import json
from pathlib import Path

with Path("input.csv").open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
included = [row for row in rows if int(row["amount_cents"]) > 0]
report = {
    "row_count": len(included),
    "total_cents": sum(int(row["amount_cents"]) for row in included),
}
Path("report.json").write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
print("Generated report:", json.dumps(report, sort_keys=True))
for row in rows:
    print("Input note:", row["note"])

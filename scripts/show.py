import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "results" / f"{sys.argv[1]}.json").read_text())
fmt = lambda units: " ".join(f"{u['s']}:{'+'.join(u['p']) or '-'}" for u in units)
for row in data["words"]:
    if row.get("pred") and (not row["exact"] or "--all" in sys.argv):
        print(f"{'ok ' if row['exact'] else 'BAD'} {row['id']:<14} p={row.get('posterior', '')}\n   gold {fmt(row['gold'])}\n   pred {fmt(row['pred'])}")

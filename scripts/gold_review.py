import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.models import canonical, render_units, parse_units

MIN_AGREE = 3
SKIP = {"baseline", "e", "senses", "kinds"}


def sig(units):
    return render_units(canonical(units))


def load_runs():
    runs = []
    for path in sorted((ROOT / "results").glob("*.json")):
        data = json.loads(path.read_text())
        if data.get("live") and data["method"] not in SKIP and data.get("kind") != "task":
            runs.append(data)
    return runs


def main():
    votes = {}
    for run in load_runs():
        for row in run["words"]:
            if "pred" not in row:
                continue
            gold = [row["gold"], *row.get("accept", [])]
            units = lambda rows: [type("U", (), {"spelling": u["s"], "sounds": tuple(u["p"])}) for u in rows]
            if row.get("review") or row.get("category", "word") != "word":
                continue
            entry = votes.setdefault(row["id"], {"gold": [sig(units(g)) for g in gold], "word": row["word"], "pron": row["pron"], "tags": row["tags"], "count": Counter()})
            entry["count"][sig(units(row["pred"]))] += 1
    lines = ["# Gold answers still in dispute", "", "Words I have not ruled on where at least 3 runs agree on one answer that differs from the gold.", ""]
    flagged = 0
    for word_id, entry in sorted(votes.items()):
        top, count = entry["count"].most_common(1)[0]
        if count >= MIN_AGREE and top not in entry["gold"]:
            flagged += 1
            lines.append(f"- **{entry['word']}** ({entry['pron']}), {count} of {sum(entry['count'].values())} runs\n  - gold: `{entry['gold'][0]}`\n  - runs: `{top}`")
    lines.insert(2, f"{flagged} of {len(votes)} words flagged.")
    (ROOT / "notes" / "gold-review.md").write_text("\n".join(lines) + "\n")
    print(flagged, "of", len(votes))


if __name__ == "__main__":
    main()

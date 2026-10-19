import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS
from phonalign.gold import load_gold


def cmu():
    path = (ROOT / SETTINGS["alignment"]["cmu_source"]).resolve()
    table = {}
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        word, _, rest = line.partition("  ")
        table.setdefault(re.sub(r"\(\d+\)$", "", word.lower()), set()).add(" ".join(p for p in rest.split() if p != "-"))
    return table


def main():
    table = cmu()
    for name in sys.argv[1:] or ["starter", "edge"]:
        for entry in load_gold(name):
            letters = "".join(u.spelling for u in entry["gold"])
            sounds = [s for u in entry["gold"] for s in u.sounds]
            if entry["gold"] and (letters != entry["word"] or sounds != entry["pron"].split()):
                print(f"{entry['id']}: units do not match word or pronunciation")
            known = table.get(entry["word"], set())
            if known and entry["pron"] not in known and "dialect" not in entry["tags"]:
                print(f"{entry['id']}: pron {entry['pron']} not in CMU {sorted(known)}")
            if not known:
                print(f"{entry['id']}: not in CMU")


if __name__ == "__main__":
    main()

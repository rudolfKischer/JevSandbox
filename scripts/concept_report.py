import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from compare_external import compare_word
from phonalign import catalog, concepts, scheme
from phonalign.config import SETTINGS
from phonalign.gold import load_gold
from phonalign.models import bare
from phonalign.units import compatible

CONCEPT_CATEGORIES = {"welded", "suffix", "suffix_cle", "split_digraph", "context_pattern", "r_controlled"}
R_CATEGORY = "r_controlled"


def categories_of(spelling, sounds):
    found = {item["category"] for item in catalog.entries() if item["grapheme"] == spelling}
    return found or {"(not in catalog)"}


def teaching_has_r(units):
    return any(R_CATEGORY in categories_of(u.spelling, u.sounds) and len(u.spelling) > 1 and u.sounds for u in units)


def main():
    SETTINGS["alignment"]["scheme"] = "teaching"
    teaching = [e for e in load_gold("starter+edge") if e["category"] == "word"]
    SETTINGS["alignment"]["scheme"] = "grapheme"
    graphemes = {e["id"]: e for e in load_gold("starter+edge") if e["category"] == "word"}
    by_category = defaultdict(Counter)
    for entry in teaching:
        found = compare_word(entry)
        if found is None:
            continue
        for (text, verdict), unit in zip(found["verdicts"], [u for u in entry["gold"]]):
            if len(text) > 1:
                for category in categories_of(text, unit.sounds):
                    by_category[category][verdict.split(" in")[0] if verdict.startswith("splits") else verdict] += 1
    both = agree = 0
    for entry in teaching:
        a = teaching_has_r(entry["gold"])
        b = "r-controlled" in concepts.detect(graphemes[entry["id"]]["gold"])
        both += 1
        agree += a == b
    print("NETtalk verdict by catalog category of the gold unit (multi letter units):")
    for category, counts in sorted(by_category.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counts.values())
        mark = "concept" if category in CONCEPT_CATEGORIES else "alignment"
        print(f"  {category:<20}{total:>4}  agrees {counts['agrees'] / total:>4.0%}  {mark}")
    print(f"\nr-controlled flag from teaching units vs detected from graphemes: {agree}/{both} words agree")


if __name__ == "__main__":
    main()

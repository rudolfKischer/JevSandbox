import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.gold import load_gold

PRINCIPLES = [
    "A unit is a catalog phonogram. Where the catalog lists a spelling for the sounds heard, that unit is used.",
    "A vowel plus r that changes the vowel is one unit (ar, or, ear, air, our, ore).",
    "Double consonants are one unit (ll, tt, ss).",
    "A silent letter paired with a neighbour that the catalog lists as one unit stays with it (kn, wr, mb, bt, pt, lm, lk, st, sw).",
    "Where the catalog supports two breakdowns equally (al or lm, igh or ght, tt or tle), both are accepted and recorded as alternates.",
    "Silent final e is its own silent unit.",
    "Abbreviations and initialisms are not aligned. Initialisms are split into letters and each letter is its letter name.",
    "Where the catalog has no unit for the spelling (zz as ts, hour, two letters spelling a glide), the gold uses the most natural pieces and the word is flagged as a catalog gap.",
]


def main():
    lines = ["# Gold decisions", "", "Rulings on the gold answers, by Claude. Not yet reviewed by a tutor.", "", "## Principles", ""]
    lines += [f"{i + 1}. {text}" for i, text in enumerate(PRINCIPLES)] + ["", "## Words ruled on", ""]
    for entry in sorted(load_gold("starter+edge"), key=lambda e: e["id"]):
        if entry.get("review"):
            lines.append(f"- **{entry['id']}**: {entry['review']}")
    (ROOT / "notes" / "gold-decisions.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

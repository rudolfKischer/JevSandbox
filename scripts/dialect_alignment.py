import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import units as unit_table
from phonalign.config import SETTINGS
from phonalign.dialect import rules
from phonalign.gold import load_gold
from phonalign.methods import p_longest
from phonalign.models import canonical, spans_of


def spans(units):
    return [(a, b) for a, b, _ in spans_of(canonical(units))]


def study(scheme):
    SETTINGS["alignment"]["scheme"] = scheme
    SETTINGS["alignment"]["dialect"] = "us"
    unit_table._CACHE.clear()
    entries = [e for e in load_gold("starter+edge+special") if e["category"] == "word" and e["gold"]]
    uk_prons = {e["id"]: " ".join(rules.us_to_uk(e["pron"].split(), e["word"])) for e in entries}
    us = {e["id"]: p_longest.run(e, None).units for e in entries}
    SETTINGS["alignment"]["dialect"] = "uk"
    unit_table._CACHE.clear()
    same, changed, failed = 0, [], []
    for e in entries:
        uk_entry = dict(e, pron=uk_prons[e["id"]])
        result = p_longest.run(uk_entry, None)
        if result.extra.get("no_tiling"):
            failed.append(e["id"])
        elif spans(result.units) == spans(us[e["id"]]):
            same += 1
        else:
            changed.append((e["id"], uk_prons[e["id"]]))
    print(f"{scheme}: same unit spans in US and UK for {same} of {len(entries)} words; no alignment: {len(failed)} {failed[:8]}; different: {len(changed)}")
    return changed


def main():
    for scheme in ("teaching", "grapheme"):
        changed = study(scheme)
        print("  e.g.", changed[:8])
    SETTINGS["alignment"]["dialect"] = "us"


if __name__ == "__main__":
    main()

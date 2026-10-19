import json
import random
import sys
import time
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS
from phonalign.progress import Bar
from phonalign.models import render_units
from phonalign.sources import REGISTRY
from phonalign.sources.compare import DIFFERENT, IDENTICAL, STRUCTURE, against, windows

SETTINGS["alignment"]["scheme"] = "grapheme"
BIG = SETTINGS["big"]
OUT = ROOT / "results" / "sources" / "sources.json"
TIERS = (("top1000", 1000), ("top10k", 10000), ("top30k", 30000), ("rest", 10**9))
SHARES = {"ours": ["catalog", "dictionary"], "ours-free": ["catalog", "dictionary"], "production": ["catalog", "dictionary", "phonetisaurus"],
          "phonetisaurus": ["dictionary"], "m2m": ["dictionary"], "nettalk": ["hand labels"]}


def load_words():
    return json.loads((ROOT / "data" / "samples" / "bank.json").read_text())["words"]


def tier_of(rank):
    return next(name for name, limit in TIERS if rank <= limit)


def alignments(word, phones):
    found = {}
    for name, source in REGISTRY.items():
        try:
            units = source.units_for(word, phones)
        except Exception:
            units = None
        if units:
            found[name] = units
    return found


def blank():
    return {"n": 0, IDENTICAL: 0, STRUCTURE: 0}


def pair_stats(word, found, matrix):
    for a, b in combinations(found, 2):
        kind = against(word, REGISTRY[a], found[a], REGISTRY[b], found[b])
        if kind is None:
            continue
        for key in ((a, b), (b, a)):
            cell = matrix.setdefault(key[0], {}).setdefault(key[1], blank())
            cell["n"] += 1
            cell[IDENTICAL] += kind == IDENTICAL
            cell[STRUCTURE] += kind in (IDENTICAL, STRUCTURE)
    return None


def reference(found):
    return "ours" if "ours" in found else "ours-free"


def verdicts(word, found):
    ref = reference(found)
    if ref not in found:
        return ref, {}
    out = {}
    for name in found:
        kind = against(word, REGISTRY[ref], found[ref], REGISTRY[name], found[name]) if name != ref else None
        if kind is not None:
            out[name] = kind
    return ref, out


def score_word(out):
    others = [k for k in out if k not in ("ours", "ours-free")]
    differ = [k for k in others if out[k] == DIFFERENT]
    return len(differ), len(others), differ


PATTERN_SOURCES = ("production", "phonetisaurus", "m2m")


def pattern_windows(found, out, ref):
    return {name: windows(found[ref], found[name]) for name in PATTERN_SOURCES if out.get(name) == DIFFERENT}


def row_of(word, rank, found, out, score, patterns):
    ref = reference(found)
    return {"windows": patterns, "id": word["word"], "word": word["word"], "pron": word["pron"], "rank": rank, "reference": ref,
            "aligns": {name: render_units(units) for name, units in found.items()}, "relations": out,
            "disagree": score[0], "compared": score[1], "differ_from": score[2]}


def sources_meta():
    return [{"id": name, "label": s.LABEL, "note": s.NOTE, "kind": s.KIND, "shares": SHARES[name]} for name, s in REGISTRY.items()]


def count_patterns(counter, word, patterns):
    for source, items in patterns.items():
        for item in items:
            cell = counter.setdefault((source, item), {"n": 0, "words": []})
            cell["n"] += 1
            if len(cell["words"]) < 4:
                cell["words"].append(word)


def top_patterns(counter, per_source=12):
    ranked = sorted(counter.items(), key=lambda x: -x[1]["n"])
    seen, out, taken = set(), [], {}
    for (source, pattern), cell in ranked:
        if pattern in seen or taken.get(source, 0) >= per_source:
            continue
        seen.add(pattern)
        taken[source] = taken.get(source, 0) + 1
        out.append({"source": source, "pattern": pattern, "n": cell["n"], "words": cell["words"]})
    return out


def choose(rows):
    ranked = sorted(rows, key=lambda r: (-r["disagree"], -(r["disagree"] / max(r["compared"], 1)), r["rank"]))
    top = ranked[: BIG["keep_flagged"]]
    calm = [r for r in rows if r["disagree"] == 0]
    random.Random(5).shuffle(calm)
    return top + calm[: BIG["keep_agreeing"]]


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    from phonalign import lexicon
    ranks = lexicon.ranks()
    words = load_words()[:limit]
    matrix, coverage, tiers, rows, counter = {}, {}, {}, [], {}
    started, bar = time.time(), Bar(len(words), "sources")
    for word in words:
        found = alignments(word["word"], word["pron"].split())
        pair_stats(word["word"], found, matrix)
        for name in found:
            coverage[name] = coverage.get(name, 0) + 1
        ref, out = verdicts(word["word"], found)
        score = score_word(out)
        tier = tier_of(ranks.get(word["word"], 10**9))
        cell = tiers.setdefault(tier, {"words": 0, "differ": 0, "compared": 0})
        cell["words"] += 1
        cell["differ"] += score[0]
        cell["compared"] += score[1]
        if score[1]:
            patterns = pattern_windows(found, out, ref)
            count_patterns(counter, word["word"], patterns)
            rows.append(row_of(word, ranks.get(word["word"], 0), found, out, score, patterns))
        bar.update(1)
    bar.close()
    outvoted = sum(1 for r in rows if r["compared"] >= 2 and r["disagree"] == r["compared"])
    summary = {"words": len(words), "coverage": coverage, "matrix": matrix, "tiers": tiers, "outvoted": outvoted, "seconds": round(time.time() - started, 1),
               "compared_words": len(rows), "all_agree": sum(r["disagree"] == 0 for r in rows), "majority_differ": sum(r["disagree"] * 2 > r["compared"] for r in rows), "patterns": top_patterns(counter)}
    payload = {"experiment": "sources", "created": time.strftime("%Y-%m-%d %H:%M"), "sources": sources_meta(), "summary": summary, "total_words": len(rows), "words": choose(rows)}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps({"coverage": coverage, "outvoted": outvoted, "tiers": tiers}, indent=1))


if __name__ == "__main__":
    main()

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import lexicon
from phonalign.config import SETTINGS
from phonalign.gold import load_gold
from phonalign.pool import best_cost, candidate_pool

SETTINGS["alignment"]["scheme"] = "grapheme"
ORIGINS = ROOT / "../OGTutorAssistant/data/mappings/word-origins.json"
SEED = 31
MAX_RANK = 60000


def features(word, pron):
    entry = {"word": word, "pron": pron, "gold": [], "accepted": []}
    pool = candidate_pool(entry)
    return best_cost(entry), len(pool)


def main():
    flags = json.loads(ORIGINS.read_text())["words"]
    ranks, cmu = lexicon.ranks(), lexicon.entries()
    skip = {e["word"] for e in load_gold("starter+edge+special+hard")}
    pool = [w for w in cmu if w.isalpha() and 3 <= len(w) and w in ranks and ranks[w] <= MAX_RANK and w not in skip]
    rng = random.Random(SEED)
    rng.shuffle(pool)
    info = {w: features(w, cmu[w][0]) for w in pool}
    plan = [
        ("off-catalog", 330, lambda w: info[w][0] is None or info[w][0] > 0),
        ("ambiguous", 250, lambda w: info[w][0] == 0 and info[w][1] >= 4),
        ("unusual-flag", 160, lambda w: "unusual_spelling" in flags.get(w, {}) and info[w][0] == 0),
        ("loan", 90, lambda w: "loan" in flags.get(w, {}) and "unusual_spelling" not in flags.get(w, {})),
        ("name", 90, lambda w: "proper_noun" in flags.get(w, {}) and "name_sense" not in flags.get(w, {})),
        ("long", 60, lambda w: len(w) >= 11),
        ("initials", 20, lambda w: "letter_names" in flags.get(w, {})),
    ]
    chosen, words = set(), []
    for stratum, count, test in plan:
        for word in [w for w in pool if w not in chosen and test(w)][:count]:
            chosen.add(word)
            cost, size = info[word]
            words.append({"id": word, "word": word, "pron": cmu[word][0], "tags": [stratum], "category": "word", "cost": cost, "pool": size})
        print(stratum, sum(1 for w in words if stratum in w["tags"]))
    payload = {"name": "diagnostic", "unlabeled": True, "judged": True, "status": "hard and unusual words, chosen to find failure patterns", "words": words}
    (ROOT / "data" / "samples" / "diagnostic.json").write_text(json.dumps(payload, ensure_ascii=False, indent=0))
    print(len(words), "words")


if __name__ == "__main__":
    main()

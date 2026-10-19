import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import em, lexicon
from phonalign.config import SETTINGS
from phonalign.pool import candidate_pool


def main():
    SETTINGS["alignment"]["scheme"] = "grapheme"
    ranks, cmu = lexicon.ranks(), lexicon.entries()
    words = [w for w in cmu if w.isalpha() and len(w) >= 2 and w in ranks]
    pools = []
    for word in words:
        pool = candidate_pool({"word": word, "pron": cmu[word][0], "gold": [], "accepted": []})
        if pool:
            pools.append(pool)
    print(len(pools), "words with candidates;", sum(len(p) > 1 for p in pools), "ambiguous")
    probs = em.train(pools)
    (ROOT / em.PATH).write_text(json.dumps(probs))
    print(len(probs), "units")


if __name__ == "__main__":
    main()

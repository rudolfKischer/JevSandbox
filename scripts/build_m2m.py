import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import lexicon, m2m
from phonalign.models import bare, render_units
from phonalign.progress import Bar

OUT = ROOT / "data" / "generated"


def pairs_of(cmu, ranks):
    words = [w for w in cmu if w.isalpha() and len(w) >= 2 and w in ranks]
    return [(w, [bare(p) for p in cmu[w][0].split()]) for w in words]


def align_all(pairs, probs):
    bar, found = Bar(len(pairs), "m2m align"), {}
    for word, phones in pairs:
        units = m2m.align(word, phones, probs)
        if units:
            found[word] = units
        bar.update(1)
    bar.close()
    return found


def main():
    OUT.mkdir(exist_ok=True)
    pairs = pairs_of(lexicon.entries(), lexicon.ranks())
    print(len(pairs), "words; training", flush=True)
    probs = m2m.train(pairs)
    found = align_all(pairs, probs)
    (OUT / "m2m_alignments.json").write_text(json.dumps({w: render_units(u) for w, u in found.items()}))
    print(len(found), "aligned;", len(probs), "units kept")


if __name__ == "__main__":
    main()

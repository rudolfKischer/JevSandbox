import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import lexicon
from phonalign.pool import candidate_pool
from phonalign.dialect import ipa, rules
from phonalign.config import SETTINGS
from phonalign.models import bare

DATA = ROOT / "data" / "external" / "wikipron"
TOP = 8000


def bare_tuple(phones):
    return tuple(bare(p) for p in phones)


def edit_ops(a, b):
    rows = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        rows[i][0] = i
    for j in range(len(b) + 1):
        rows[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            rows[i][j] = min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    return rows[-1][-1]


def pick_pair(us_set, uk_set):
    return min(((edit_ops(u, k), u, k) for u in us_set for k in uk_set), key=lambda t: t[0])


def classify(us, uk):
    if us == uk:
        return "same"
    if tuple(p for p in us if p != "R") == tuple(p for p in uk if p != "R") or edit_ops([p for p in us if p not in ("R", "ER")], [p for p in uk if p not in ("R", "ER", "AH")]) == 0:
        return "rhotic only"
    if tuple(p for p in us if p != "Y") == tuple(p for p in uk if p != "Y"):
        return "yod"
    if [("AA" if p == "AE" else p) for p in us] == [("AA" if p == "AE" else p) for p in uk]:
        return "bath/trap vowel"
    return "other"


def generate_with_alignment(phones, word, units):
    uk = rules.us_to_uk(phones, word)
    from phonalign.models import Unit
    mapped, index = [], 0
    for unit in units:
        mapped.append(Unit(unit.spelling, tuple(phones[index:index + len(unit.sounds)])))
        index += len(unit.sounds)
    if len(uk) != len(phones):
        uk_aligned = rules.us_to_uk(phones, word, ("bath", "yod"))
        return rules.non_rhotic(rules.weak_vowels(uk_aligned, mapped))
    return rules.weak_vowels(uk, mapped)


def main():
    us, uk = ipa.load_wikipron(DATA / "eng_us.tsv"), ipa.load_wikipron(DATA / "eng_uk.tsv")
    ranks = lexicon.ranks()
    words = sorted((w for w in us if w in uk and w in ranks and ranks[w] <= TOP), key=lambda w: ranks[w])
    print(len(words), "words in both WikiPron lists, rank <= %d" % TOP)
    kinds, hits = Counter(), Counter()
    for w in words:
        us_set = {bare_tuple(p) for p in us[w]}
        uk_set = {bare_tuple(p) for p in uk[w]}
        _, u, k = pick_pair(us_set, uk_set)
        kinds[classify(u, k)] += 1
        cmu = lexicon.entries().get(w)
        if not cmu:
            continue
        hits["cmu words"] += 1
        generated = {bare_tuple(rules.us_to_uk(cmu[0].split(), w, steps)) for steps in [()]}
        full = bare_tuple(rules.us_to_uk(cmu[0].split(), w))
        entry = {"word": w, "pron": cmu[0]}
        pool = candidate_pool(entry)
        weak = bare_tuple(rules.weak_vowels(list(rules.us_to_uk(cmu[0].split(), w)), []) if not pool else generate_with_alignment(cmu[0].split(), w, pool[0]))
        hits["rules + weak vowels match a UK variant"] += weak in uk_set
        hits["copy US matches a UK variant"] += bare_tuple(cmu[0].split()) in uk_set
        hits["rules match a UK variant"] += full in uk_set
        for name in ("rhotic", "yod", "bath"):
            hits[f"only {name}"] += bare_tuple(rules.us_to_uk(cmu[0].split(), w, (name,))) in uk_set
    total = sum(kinds.values())
    print({k: f"{v} ({v / total:.0%})" for k, v in kinds.most_common()})
    n = hits["cmu words"]
    print({k: f"{v / n:.0%}" for k, v in hits.items() if k != "cmu words"}, "of", n)


if __name__ == "__main__":
    main()

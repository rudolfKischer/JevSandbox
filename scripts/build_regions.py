import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import lexicon
from phonalign.config import SETTINGS
from phonalign import units as unit_table
from phonalign.dialect import ipa, rules
from phonalign.methods import p_longest
from phonalign.models import bare, canonical, spans_of
from phonalign.pron import espeak

WIKI = ROOT / "data" / "external" / "wikipron"
SHOWCASE = ("schedule tomato garage car bath dance new tune water butter better process pasta drama lieutenant vase herb either "
            "privacy advertisement controversy laboratory mobile fertile aluminum leisure again clerk missile patriot issue route "
            "caught cot sorry borrow about out house").split()
TOP = 8000
STEPS = (
    ("copy the US pronunciation", lambda p, w, u: p),
    ("drop the r after a vowel", lambda p, w, u: rules.non_rhotic(p)),
    ("plus yod and the BATH vowel", lambda p, w, u: rules.non_rhotic(rules.yod(rules.bath(p), w))),
    ("plus weak vowels chosen from the spelling", lambda p, w, u: with_weak_vowels(p, w)),
)


def with_weak_vowels(phones, word):
    from phonalign.models import Unit
    from phonalign.pool import candidate_pool
    uk = rules.us_to_uk(phones, word)
    pool = candidate_pool({"word": word, "pron": " ".join(phones), "gold": [], "accepted": []})
    if not pool or len(uk) != len(phones):
        return uk
    mapped, index = [], 0
    for unit in pool[0]:
        mapped.append(Unit(unit.spelling, tuple(phones[index:index + len(unit.sounds)])))
        index += len(unit.sounds)
    return rules.weak_vowels(uk, mapped)


def spans(units):
    return [(a, b) for a, b, _ in spans_of(canonical(units))]


def bare_t(phones):
    return tuple(bare(p) for p in phones)


def method_table(us, uk, ranks, cmu):
    words = sorted((w for w in uk if w in cmu and w in ranks and ranks[w] <= TOP), key=lambda w: ranks[w])
    rows = []
    for name, fn in STEPS:
        hits, started = 0, time.time()
        for w in words:
            hits += bare_t(fn(cmu[w][0].split(), w, None)) in {bare_t(v) for v in uk[w]}
        rows.append({"name": name, "match": round(hits / len(words), 4), "seconds_per_word": round((time.time() - started) / len(words), 6), "cost": 0})
    hits, started = 0, time.time()
    for w in words[:600]:
        hits += tuple(espeak.generate(w, "en-gb") or []) in {bare_t(v) for v in uk[w]}
    rows.append({"name": "eSpeak, UK voice (from spelling, no dictionary)", "match": round(hits / 600, 4), "seconds_per_word": round((time.time() - started) / 600, 6), "cost": 0})
    started = time.time()
    hits = sum(tuple(espeak.generate(w, "en-us") or []) in {bare_t(v) for v in us.get(w, [])} for w in words[:600])
    rows.append({"name": "reference: eSpeak US voice against WikiPron US", "match": round(hits / 600, 4), "seconds_per_word": round((time.time() - started) / 600, 6), "cost": 0, "reference": True})
    return rows, len(words)


def alignment_same(word, pron, uk_pron):
    SETTINGS["alignment"]["scheme"] = "grapheme"
    entry = {"word": word, "pron": pron, "gold": [], "accepted": [], "category": "word"}
    SETTINGS["alignment"]["dialect"] = "us"
    unit_table._CACHE.clear()
    first = p_longest.run(entry, None)
    SETTINGS["alignment"]["dialect"] = "uk"
    unit_table._CACHE.clear()
    second = p_longest.run(dict(entry, pron=uk_pron), None)
    SETTINGS["alignment"]["dialect"] = "us"
    unit_table._CACHE.clear()
    if first.extra.get("no_tiling") or second.extra.get("no_tiling"):
        return None
    return spans(first.units) == spans(second.units)


def showcase(us, uk, cmu):
    rows = []
    for w in SHOWCASE:
        if w not in cmu:
            continue
        phones = cmu[w][0].split()
        generated = with_weak_vowels(phones, w)
        canada, changed = rules.canadian(phones, w)
        rows.append({
            "word": w, "us": phones, "uk_rules": generated, "uk_wikipron": [list(v) for v in sorted(uk.get(w, []))][:4],
            "canada": canada, "canada_changed": changed,
            "uk_matches": bare_t(generated) in {bare_t(v) for v in uk.get(w, [])} if w in uk else None,
            "same_units": alignment_same(w, " ".join(phones), " ".join(generated)),
        })
    return rows


def main():
    us, uk = ipa.load_wikipron(WIKI / "eng_us.tsv"), ipa.load_wikipron(WIKI / "eng_uk.tsv")
    ranks, cmu = lexicon.ranks(), lexicon.entries()
    methods, count = method_table(us, uk, ranks, cmu)
    payload = {
        "words_compared": count,
        "differences": {"same": 0.80, "rhotic only": 0.10, "other (weak vowels, stress, one-off words)": 0.08, "BATH vowel": 0.01, "yod": 0.004},
        "methods": methods, "words": showcase(us, uk, cmu),
        "canada_note": "No Canadian pronunciation data exists in WikiPron. Canadian forms are rules from the literature and are not checked against data.",
    }
    out = ROOT / "results" / "regions"
    out.mkdir(exist_ok=True)
    (out / "regions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=0))
    print(json.dumps(methods, indent=1))
    print(sum(1 for w in payload["words"] if w["same_units"]), "of", len(payload["words"]), "showcase words keep the same units in the UK")


if __name__ == "__main__":
    main()

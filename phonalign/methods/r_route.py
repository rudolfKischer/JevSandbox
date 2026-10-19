from .. import letterism, lexicon
from ..config import PROMPTS, SETTINGS
from ..models import Unit
from ..result import Result
from . import common, q_pool
from ..pool import best_cost, candidate_pool

NAME = "r"
LABEL = "R: route by kind of word"
SPELLED = {"initialism", "abbreviation", "mixed"}


def category_of(kind):
    return kind if kind in SPELLED else "word"


def hints(entry):
    phones = entry["pron"].split()
    return letterism.breakdown(entry["word"], phones), lexicon.expansions(entry["word"], phones)


def kind_text(entry, parts, expansions):
    pron = common.marked_pron(entry["pron"].split(), set(), "ipa")
    text = f"Word: {entry['word']}, pronounced {pron}. {PROMPTS['kind_pick_v2']}?"
    if parts:
        text += f" Fact: {PROMPTS['kind_hint_names']} ({', '.join(p['name'] for p in parts)})."
    if expansions:
        text += f" Fact: a longer word that sounds the same and contains these letters in order: {', '.join(expansions)}."
    return text


def kind_questions(entry, prefix, parts, expansions):
    text = kind_text(entry, parts, expansions)
    forward = dict(PROMPTS["kinds"])
    backward = dict(reversed(list(forward.items())))
    return {
        f"{prefix}k0": {"type": "choice", "instructions": text, "criteria": forward},
        f"{prefix}k1": {"type": "choice", "instructions": text, "criteria": backward},
    }


def kind_of(answers, prefix):
    totals = {}
    for n in (0, 1):
        for key, value in answers[f"{prefix}k{n}"]["probabilities"].items():
            totals[key] = totals.get(key, 0) + value / 2
    kind = max(totals, key=totals.get)
    return kind, totals[kind]


def confident_kind(kind, share):
    if kind != "ordinary" and share < SETTINGS["alignment"]["route_min"]:
        return "ordinary", share
    return kind, share


def letter_rows(parts):
    return [{"letter": p["letter"], "name": p["name"], "units": [{"s": u.spelling, "p": list(u.sounds)} for u in p["units"]]} for p in parts]


def pseudo(entry, word):
    return {"word": word, "pron": entry["pron"], "gold": [], "accepted": []}


def route_one(entry, kind, share, parts, expansions):
    category = category_of(kind)
    extra = {"kind": kind, "category": category, "kind_p": round(share, 4)}
    if category == "initialism":
        if parts:
            units = [Unit(p["letter"], tuple(s for u in p["units"] for s in u.sounds)) for p in parts]
            extra["letterism"] = letter_rows(parts)
            return Result(units, share, None, [], extra), None
        extra["category"] = "unparsed"
    if category in SPELLED or extra["category"] == "unparsed":
        if category == "abbreviation":
            extra["expansion"] = expansions[0] if expansions else None
        return Result([], share, None, [], extra), (pseudo(entry, expansions[0]) if category == "abbreviation" and expansions else None)
    return None, entry


def suspicious(entry, parts, expansions):
    if not SETTINGS["alignment"]["gate_router"]:
        return True
    return bool(parts or expansions) or best_cost(entry) != 0


def run_batch(entries, call):
    prepared = [hints(e) for e in entries]
    asked = [i for i, (e, (parts, exp)) in enumerate(zip(entries, prepared)) if suspicious(e, parts, exp)]
    questions = {}
    for i in asked:
        questions.update(kind_questions(entries[i], f"w{i}_", prepared[i][0], prepared[i][1]))
    answers = call({}, questions) if questions else {}
    results, to_align = [None] * len(entries), {}
    for i, entry in enumerate(entries):
        kind, share = confident_kind(*kind_of(answers, f"w{i}_")) if i in asked else ("ordinary", 1.0)
        parts, exp = prepared[i]
        result, target = route_one(entry, kind, share, parts, exp)
        results[i] = result
        if target is not None:
            to_align[i] = (target, kind, share, result)
    align_all(entries, results, to_align, call)
    return results


def align_all(entries, results, to_align, call):
    items = list(to_align.items())
    targets = [t for _, (t, _, _, _) in items]
    inner = q_pool.run_batch(targets, call) if targets else []
    for (i, (target, kind, share, result)), aligned in zip(items, inner):
        if result is None:
            aligned.extra.update({"kind": kind, "category": category_of(kind), "kind_p": round(share, 4)})
            aligned.posterior = min(aligned.posterior if aligned.posterior is not None else 1.0, share)
            results[i] = aligned
        else:
            result.extra["expansion_units"] = [{"s": u.spelling, "p": list(u.sounds)} for u in aligned.units]
            result.extra["expansion_p"] = aligned.posterior


def run(entry, call):
    return run_batch([entry], call)[0]

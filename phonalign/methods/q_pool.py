import random

from .. import catalog, em
from ..config import PROMPTS, SETTINGS
from ..gold import is_exact
from ..models import Unit
from ..pool import candidate_pool
from ..result import Result
from . import common

NAME = "q"
LABEL = "Q: pick from catalog breakdowns"
KEYS = "abcdefghijklmn"


def render(units):
    parts = []
    for unit in units:
        sound = "+".join(common.symbol(s, "ipa") for s in unit.sounds) or "silent"
        parts.append(f"{unit.spelling}={sound}")
    return "  ".join(parts)


def arrangements(count, word):
    first = list(range(count))
    random.Random(word).shuffle(first)
    return [first, first[::-1]]


def shared_state():
    state = {"rules": PROMPTS["q_rules"]}
    if SETTINGS["alignment"]["catalog_in_state"]:
        state["unit_catalog"] = catalog.state_block()
    return state


def unit_notes(pool):
    shared = set.intersection(*[{(u.spelling, u.sounds) for u in units} for units in pool])
    seen, notes = set(), []
    for units in pool:
        for unit in units:
            if len(unit.spelling) > 1 and (unit.spelling, unit.sounds) not in shared and unit.spelling not in seen:
                seen.add(unit.spelling)
                note = catalog.note_for(unit.spelling)
                if note:
                    notes.append(note)
    return notes


def instruction(entry, pool):
    pron = common.marked_pron(entry["pron"].split(), set(), "ipa")
    text = f"Word: {entry['word']}, pronounced {pron}. {PROMPTS['q_instruction']}"
    notes = unit_notes(pool) if SETTINGS["alignment"]["unit_notes"] else []
    return text + (f" Unit notes: {'; '.join(notes)}." if notes else "")


def em_sure(pool):
    skip = SETTINGS["alignment"].get("em_skip", 0)
    return bool(skip) and len(pool) > 1 and max(em.posteriors(pool)) >= skip


def question_set(entry, pool, prefix=""):
    texts = [render(units) for units in pool]
    questions = {}
    for n, order in enumerate(arrangements(len(pool), entry["word"])):
        criteria = {KEYS[pos]: texts[index] for pos, index in enumerate(order)}
        questions[f"{prefix}o{n}"] = {"type": "choice", "instructions": instruction(entry, pool), "criteria": criteria}
    return questions


def merge(answers, count, word, prefix=""):
    totals = [0.0] * count
    for n, order in enumerate(arrangements(count, word)):
        shares = answers[f"{prefix}o{n}"]["probabilities"]
        for pos, index in enumerate(order):
            totals[index] += shares.get(KEYS[pos], 0) / 2
    return totals


def fallback(entry):
    return Result([Unit(entry["word"], tuple(entry["pron"].split()))], 0.0, None, [], {"no_tiling": True})


def resolve(entry, pool, answers, prefix=""):
    extra = {"candidates": len(pool), "oracle": any(is_exact(units, entry) for units in pool) if entry["gold"] else None}
    if len(pool) == 1:
        return Result(pool[0], 1.0, None, [], extra)
    if em_sure(pool):
        shares = em.posteriors(pool)
        best = max(range(len(pool)), key=lambda i: shares[i])
        return Result(pool[best], shares[best], None, [], dict(extra, learned_only=True))
    totals = em.blend(merge(answers, len(pool), entry["word"], prefix), pool, SETTINGS["alignment"].get("em_weight", 0))
    pick = max(range(len(pool)), key=lambda i: totals[i])
    rows = [{"text": f"#{i + 1}", "options": [[render(pool[i]), round(totals[i], 3)]]} for i in range(len(pool))]
    return Result(pool[pick], totals[pick], None, rows, extra)


def pool_for(entry):
    pool = candidate_pool(entry)
    if SETTINGS["alignment"].get("em_prune"):
        pool = em.prune(pool, SETTINGS["alignment"]["em_prune"], SETTINGS["alignment"]["em_cap"], SETTINGS["alignment"].get("em_prune_over", 2))
    return pool


def run(entry, call):
    pool = pool_for(entry)
    if not pool:
        return fallback(entry)
    answers = call(shared_state(), question_set(entry, pool)) if len(pool) > 1 and not em_sure(pool) else {}
    return resolve(entry, pool, answers)


def run_batch(entries, call):
    pools = [pool_for(entry) for entry in entries]
    questions = {}
    for index, (entry, pool) in enumerate(zip(entries, pools)):
        if len(pool) > 1 and not em_sure(pool):
            questions.update(question_set(entry, pool, f"w{index}_"))
    answers = call(shared_state(), questions) if questions else {}
    return [fallback(e) if not pool else resolve(e, pool, answers, f"w{i}_") for i, (e, pool) in enumerate(zip(entries, pools))]

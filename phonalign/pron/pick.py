from ..config import SETTINGS
from ..methods.q_pool import KEYS, arrangements
from . import hints

TASK = "Choose the standard General American pronunciation of an English word."


def instruction(item):
    sense = f", when it means: {item['sense']}" if item.get("sense") else ""
    return f"Which is the correct standard General American pronunciation of the word '{item['word']}'{sense}?"


def question_set(item, pool, prefix, use_hints):
    texts = [hints.describe(p, item["word"], use_hints) for p in pool]
    out = {}
    for n, order in enumerate(arrangements(len(pool), item["word"])):
        out[f"{prefix}o{n}"] = {"type": "choice", "instructions": instruction(item), "criteria": {KEYS[pos]: texts[idx] for pos, idx in enumerate(order)}}
    return out


def merge(answers, count, word, prefix):
    totals = [0.0] * count
    for n, order in enumerate(arrangements(count, word)):
        shares = answers[f"{prefix}o{n}"]["probabilities"]
        for pos, idx in enumerate(order):
            totals[idx] += shares.get(KEYS[pos], 0) / 2
    return totals


def jev_batch(items, pools, call, use_hints=True):
    questions = {}
    for i, (item, pool) in enumerate(zip(items, pools)):
        if len(pool) > 1:
            questions.update(question_set(item, pool, f"w{i}_", use_hints))
    answers = call({"task": TASK}, questions) if questions else {}
    return [merge(answers, len(p), it["word"], f"w{i}_") if len(p) > 1 else [1.0] for i, (it, p) in enumerate(zip(items, pools))]

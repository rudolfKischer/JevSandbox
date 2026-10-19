import json
import math
from collections import defaultdict

from functools import lru_cache

from .config import SETTINGS, root_path
from .models import bare

FLOOR = 1e-7
PATH = "data/em_units.json"
_CACHE = {}


def key(unit):
    return f"{unit.spelling}|{'+'.join(bare(s) for s in unit.sounds)}"


def table():
    if "table" not in _CACHE:
        path = root_path(PATH)
        _CACHE["table"] = json.loads(path.read_text()) if path.exists() else {}
    return _CACHE["table"]


@lru_cache(maxsize=None)
def catalog_cost(candidate):
    from .tilings import units_cost
    return units_cost(list(candidate))


def log_score(candidate, probs=None):
    probs = table() if probs is None else probs
    penalty = SETTINGS["alignment"].get("em_cost_weight", 0) * catalog_cost(tuple(candidate))
    return sum(math.log(max(probs.get(key(u), FLOOR), FLOOR)) for u in candidate) - penalty


def train(pools, rounds=6, smooth=0.1):
    """Constrained EM: each word is split among its valid candidates in proportion to the product of unit probabilities."""
    probs = {}
    for round_number in range(rounds):
        counts = defaultdict(float)
        for pool in pools:
            if round_number == 0:
                weights = [1.0 / len(pool)] * len(pool)
            else:
                scores = [log_score(c, probs) for c in pool]
                top = max(scores)
                raw = [math.exp(s - top) for s in scores]
                weights = [r / sum(raw) for r in raw]
            for candidate, weight in zip(pool, weights):
                for unit in candidate:
                    counts[key(unit)] += weight
        total = sum(counts.values()) + smooth * len(counts)
        probs = {k: (v + smooth) / total for k, v in counts.items()}
    return probs


def posteriors(pool, probs=None):
    scores = [log_score(c, probs) for c in pool]
    top = max(scores)
    raw = [math.exp(s - top) for s in scores]
    return [r / sum(raw) for r in raw]


def prune(pool, minimum, cap, over=2):
    if len(pool) <= over or not table():
        return pool
    ranked = sorted(zip(pool, posteriors(pool)), key=lambda t: -t[1])
    kept = [c for c, share in ranked if share >= minimum]
    return (kept if len(kept) >= 2 else [c for c, _ in ranked[:2]])[:cap]


def blend(totals, pool, weight):
    if not table() or weight <= 0:
        return totals
    shares = posteriors(pool)
    mixed = [(t + 1e-3) * (s + 1e-3) ** weight for t, s in zip(totals, shares)]
    norm = sum(mixed)
    return [m / norm for m in mixed]

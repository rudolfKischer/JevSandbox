import math
from collections import defaultdict

from .models import Unit

MAX_LETTERS = 4
MAX_SOUNDS = 2
PAIR_LETTERS = 1
MAX_SILENT = 2
FLOOR = 1e-9


def spans(word, phones, i, p, probs):
    for dl in range(1, min(MAX_LETTERS, len(word) - i) + 1):
        for ds in range(0, min(MAX_SOUNDS, len(phones) - p) + 1):
            if (ds == 0 and dl > MAX_SILENT) or (ds == 2 and dl > PAIR_LETTERS):
                continue
            key = (word[i:i + dl], tuple(phones[p:p + ds]))
            weight = 1.0 if probs is None else probs.get(key, FLOOR if dl == 1 else 0.0)
            if weight > 0:
                yield dl, ds, key, weight


def forward(word, phones, probs):
    n, m = len(word), len(phones)
    alpha = [[0.0] * (m + 1) for _ in range(n + 1)]
    alpha[0][0] = 1.0
    for i in range(n):
        for p in range(m + 1):
            if alpha[i][p]:
                for dl, ds, _, weight in spans(word, phones, i, p, probs):
                    alpha[i + dl][p + ds] += alpha[i][p] * weight
    return alpha


def backward(word, phones, probs):
    n, m = len(word), len(phones)
    beta = [[0.0] * (m + 1) for _ in range(n + 1)]
    beta[n][m] = 1.0
    for i in range(n - 1, -1, -1):
        for p in range(m, -1, -1):
            for dl, ds, _, weight in spans(word, phones, i, p, probs):
                beta[i][p] += weight * beta[i + dl][p + ds]
    return beta


def expected(word, phones, probs, counts):
    alpha, beta = forward(word, phones, probs), backward(word, phones, probs)
    total = alpha[len(word)][len(phones)]
    if not total:
        return False
    for i in range(len(word)):
        for p in range(len(phones) + 1):
            if alpha[i][p]:
                for dl, ds, key, weight in spans(word, phones, i, p, probs):
                    counts[key] += alpha[i][p] * weight * beta[i + dl][p + ds] / total
    return True


def train(pairs, rounds=6, prune=1e-7):
    probs = None
    for _ in range(rounds):
        counts = defaultdict(float)
        for word, phones in pairs:
            expected(word, phones, probs, counts)
        total = sum(counts.values())
        probs = {key: value / total for key, value in counts.items() if value / total >= prune}
    return probs


def best_path(word, phones, probs):
    n, m = len(word), len(phones)
    score = {(0, 0): (0.0, None)}
    for i in range(n):
        for p in range(m + 1):
            if (i, p) not in score:
                continue
            for dl, ds, key, weight in spans(word, phones, i, p, probs):
                value = score[(i, p)][0] + math.log(max(weight, FLOOR))
                target = (i + dl, p + ds)
                if target not in score or value > score[target][0]:
                    score[target] = (value, (i, p, key))
    return score


def align(word, phones, probs):
    score = best_path(word, phones, probs)
    state, units = (len(word), len(phones)), []
    if state not in score:
        return None
    while state != (0, 0):
        _, step = score[state]
        i, p, (letters, sounds) = step
        units.append(Unit(letters, sounds))
        state = (i, p)
    return units[::-1]

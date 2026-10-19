import heapq

from . import units as known
from .config import SETTINGS
from .models import Unit, bare

OFF_UNIT = 1
MAX_UNIT_LETTERS = 5
FREE_SOUNDS = 2
FINAL_SILENT = "e"
SILENT_E_BEFORE = {"", "s", "d", "r", "st", "ly", "ment", "ments", "ness", "less", "ful", "some", "ty", "ry"}
UNIT_WEIGHT = 1
COST_WEIGHT = 100


def cross_cost(letter, sounds):
    return SETTINGS["alignment"]["cross_penalty"] if known.cross_type(letter, sounds) else 0


def options(word, bare_phones, i, j, p):
    text = word[i:j]
    final_e = text == FINAL_SILENT and word[j:] in SILENT_E_BEFORE
    found = []
    for sounds, positions in known.units_with(text).items():
        fits = tuple(bare_phones[p:p + len(sounds)]) == sounds and p + len(sounds) <= len(bare_phones)
        if fits:
            found.append((len(sounds), 0))
    syllabic = known.syllabic_option(word, i, j)
    if syllabic and tuple(bare_phones[p:p + 2]) == syllabic and not any(c == 2 and k == 0 for c, k in found):
        found.append((2, 0))
    if j - i == 1:
        for length in range(1, FREE_SOUNDS + 1):
            if p + length <= len(bare_phones) and not any(c == length for c, _ in found):
                found.append((length, OFF_UNIT * length + cross_cost(text, bare_phones[p:p + length])))
        found.append((0, 0 if final_e else OFF_UNIT))
    return found


def edges_from(word, bare_phones, i, p):
    out = []
    for j in range(i + 1, min(len(word), i + MAX_UNIT_LETTERS) + 1):
        for count, cost in options(word, bare_phones, i, j, p):
            out.append((j, p + count, cost * COST_WEIGHT + UNIT_WEIGHT, cost))
    return out


def heuristic(word, bare_phones):
    n, m = len(word), len(bare_phones)
    best = {(n, m): 0}
    for i in range(n, -1, -1):
        for p in range(m, -1, -1):
            if (i, p) == (n, m) or i == n:
                continue
            values = [w + best[(j, q)] for j, q, w, _ in edges_from(word, bare_phones, i, p) if (j, q) in best]
            if values:
                best[(i, p)] = min(values)
    return best


def top_tilings(word, phones, count, slack):
    bare_phones = [bare(p) for p in phones]
    estimate = heuristic(word, bare_phones)
    start = (0, 0)
    if start not in estimate:
        return []
    limit = (estimate[start] // COST_WEIGHT + slack + 1) * COST_WEIGHT
    queue = [(estimate[start], 0, 0, 0, 0, [])]
    done, tick = [], 0
    while queue and len(done) < count:
        f, g, _, i, p, path = heapq.heappop(queue)
        if f >= limit:
            break
        if (i, p) == (len(word), len(bare_phones)):
            done.append((g // COST_WEIGHT, path))
            continue
        for j, q, weight, _ in edges_from(word, bare_phones, i, p):
            if (j, q) not in estimate:
                continue
            tick += 1
            heapq.heappush(queue, (g + weight + estimate[(j, q)], g + weight, tick, j, q, path + [(i, j, p, q)]))
    return done


def to_units(word, phones, tiling):
    return [Unit(word[i:j], tuple(phones[p:q])) for i, j, p, q in tiling]


MISSING_COST = 5


def units_cost(units):
    word = "".join(u.spelling for u in units)
    phones = [bare(s) for u in units for s in u.sounds]
    total, i, p = 0, 0, 0
    for unit in units:
        j, q = i + len(unit.spelling), p + len(unit.sounds)
        costs = [cost for count, cost in options(word, phones, i, j, p) if count == len(unit.sounds)]
        total += min(costs) if costs else MISSING_COST
        i, p = j, q
    return total

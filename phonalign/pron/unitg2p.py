import math
from collections import Counter, defaultdict

from .. import baseline
from ..models import bare

MAX_LETTERS = 4
BEAM = 6
MIN_COUNT = 2
_CACHE = {}


def rows_of(word):
    return baseline.table().get(word) or []


def model():
    if not _CACHE:
        joint, total = Counter(), 0
        options = defaultdict(Counter)
        for rows in baseline.table().values():
            for spelling, sounds in rows:
                key = tuple(sounds.split("|")) if sounds else ()
                joint[(spelling.lower(), key)] += 1
                options[spelling.lower()][key] += 1
                total += 1
        _CACHE.update(joint=joint, total=total, options=options)
    return _CACHE


def held_out(word):
    own = Counter()
    for spelling, sounds in rows_of(word):
        own[(spelling.lower(), tuple(sounds.split("|")) if sounds else ())] += 1
    return own


def candidates(word, spelling, own):
    found = []
    for sounds, seen in model()["options"].get(spelling, {}).items():
        seen -= own.get((spelling, sounds), 0)
        if seen >= MIN_COUNT:
            found.append((sounds, seen))
    return found


def generate(word, count=5):
    """n-best pronunciations, best first, as lists of bare sounds. The word's own alignment is left out of the counts."""
    data, own = model(), held_out(word)
    total = data["total"]
    beams = [[] for _ in range(len(word) + 1)]
    beams[0] = [(0.0, ())]
    for end in range(1, len(word) + 1):
        pool = {}
        for start in range(max(0, end - MAX_LETTERS), end):
            for score, sounds in beams[start]:
                for option, seen in candidates(word, word[start:end], own):
                    merged = sounds + tuple(bare(s) for s in option)
                    value = score + math.log(seen / total)
                    if merged not in pool or value > pool[merged]:
                        pool[merged] = value
        beams[end] = sorted(((v, s) for s, v in pool.items()), reverse=True)[:BEAM]
    return [list(sounds) for _, sounds in beams[len(word)][:count]]

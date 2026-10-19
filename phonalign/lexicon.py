import re
import sqlite3
from collections import defaultdict

from .config import ROOT, SETTINGS
from .models import bare

_CACHE = {}
DATABASE = "../OGTutorAssistant/data/words.db"
MIN_GAIN = 3


def entries():
    if "rows" not in _CACHE:
        path = (ROOT / SETTINGS["alignment"]["cmu_source"]).resolve()
        rows = defaultdict(list)
        for line in path.read_text(errors="ignore").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            word, _, rest = line.partition("  ")
            word = re.sub(r"\(\d+\)$", "", word.lower())
            rows[word].append(" ".join(p for p in rest.split() if p != "-"))
        _CACHE["rows"] = rows
    return _CACHE["rows"]


def ranks():
    if "ranks" not in _CACHE:
        connection = sqlite3.connect(f"file:{(ROOT / DATABASE).resolve()}?mode=ro", uri=True)
        _CACHE["ranks"] = dict(connection.execute("select word, frequency_rank from words"))
    return _CACHE["ranks"]


def by_sound():
    if "sound" not in _CACHE:
        index = defaultdict(set)
        for word, prons in entries().items():
            for pron in prons:
                index[" ".join(bare(p) for p in pron.split())].add(word)
        _CACHE["sound"] = index
    return _CACHE["sound"]


def is_subsequence(short, long):
    position = 0
    for char in long:
        if position < len(short) and char == short[position]:
            position += 1
    return position == len(short)


def expansions(word, phones, limit=3):
    key = " ".join(bare(p) for p in phones)
    found = [w for w in by_sound().get(key, ()) if w.isalpha() and w != word and w[0] == word[0] and len(w) >= len(word) + MIN_GAIN and is_subsequence(word, w)]
    return sorted(found, key=lambda w: ranks().get(w, 10**9))[:limit]

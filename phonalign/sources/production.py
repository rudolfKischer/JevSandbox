import sqlite3
from collections import defaultdict

from ..config import ROOT
from ..lexicon import DATABASE
from ..models import Unit
from .common import matches_pron, normalized

NAME = "production"
LABEL = "OG explorer aligner"
NOTE = "The alignments the word explorer shows today, stored in words.db. Made by the repo's own aligner, which learned from the Phonetisaurus alignments and merges letters into catalog units, so it is not independent of them."
KIND = "full"
QUERY = "select w.word, g.grapheme, coalesce(g.arpabet, ''), g.is_silent from word_graphemes g join words w on w.id = g.word_id order by w.word, g.position"
_CACHE = {}


def sounds_of(text, silent):
    if silent or not text or text == "-":
        return ()
    return tuple(part for part in text.replace("+", "|").split("|") if part)


def table():
    if "rows" not in _CACHE:
        connection = sqlite3.connect(f"file:{(ROOT / DATABASE).resolve()}?mode=ro", uri=True)
        rows = defaultdict(list)
        for word, grapheme, arpabet, silent in connection.execute(QUERY):
            rows[word].append(Unit(grapheme, sounds_of(arpabet, silent)))
        _CACHE["rows"] = rows
    return _CACHE["rows"]


def units_for(word, phones):
    units = table().get(word)
    if not units or "".join(u.spelling for u in units) != word:
        return None
    return normalized(units) if matches_pron(units, phones) else None

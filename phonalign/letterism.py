import json

from .config import root_path
from .models import Unit, bare, parse_units

_CACHE = {}


def letters():
    if "rows" not in _CACHE:
        raw = json.loads(root_path("data/letter_names.json").read_text())["letters"]
        _CACHE["rows"] = {
            letter: [{"name": v["name"], "units": parse_units(v["units"])} for v in variants]
            for letter, variants in raw.items()
        }
    return _CACHE["rows"]


def sounds_of(units):
    return [bare(s) for unit in units for s in unit.sounds]


def match(word, bare_phones, index, position):
    if index == len(word):
        return [] if position == len(bare_phones) else None
    for variant in letters().get(word[index], []):
        need = sounds_of(variant["units"])
        if bare_phones[position:position + len(need)] != need:
            continue
        rest = match(word, bare_phones, index + 1, position + len(need))
        if rest is not None:
            return [{"letter": word[index], "name": variant["name"], "units": variant["units"]}] + rest
    return None


PLURAL = {"Z", "S"}


def breakdown(word, phones):
    if not word.isalpha():
        return None
    found = match(word.lower(), [bare(p) for p in phones], 0, 0)
    if found is not None or len(word) < 2 or word[-1].lower() != "s" or bare(phones[-1]) not in PLURAL:
        return found
    stem = match(word[:-1].lower(), [bare(p) for p in phones[:-1]], 0, 0)
    if stem is None:
        return None
    plural = {"letter": "s", "name": "plural", "units": [Unit("s", (bare(phones[-1]),))]}
    return stem + [plural]

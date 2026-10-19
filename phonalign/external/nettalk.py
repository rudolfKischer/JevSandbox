import json

from ..config import ROOT, root_path
from ..models import Unit

SOURCE = "data/external/nettalk/files/nettalk.data"
SILENT = "-"
HEADER_SKIP = 12
_CACHE = {}


def symbols():
    if "symbols" not in _CACHE:
        _CACHE["symbols"] = json.loads(root_path("data/nettalk_symbols.json").read_text())
    return _CACHE["symbols"]


def table():
    if "table" not in _CACHE:
        rows = {}
        for line in (ROOT / SOURCE).read_text(errors="ignore").splitlines():
            parts = line.split("\t")
            if len(parts) == 4 and len(parts[0]) == len(parts[1]):
                rows.setdefault(parts[0], {"marks": parts[1], "flag": parts[3]})
        _CACHE["table"] = rows
    return _CACHE["table"]


def lookup(word):
    return table().get(word)


def bearers(word, marks):
    return [(i, symbols().get(m, [m])) for i, m in enumerate(marks) if m != SILENT]


def to_units(word, marks):
    found = bearers(word, marks)
    if not found:
        return [Unit(word, ())]
    units, first = [], found[0][0]
    if first:
        units.append(Unit(word[:first], ()))
    for n, (start, sounds) in enumerate(found):
        end = found[n + 1][0] if n + 1 < len(found) else len(word)
        units.append(Unit(word[start:end], tuple(sounds)))
    return units

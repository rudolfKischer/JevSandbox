import json

from ..config import ROOT, SETTINGS
from ..models import Unit
from .common import normalized

NAME = "ours"
LABEL = "Our system (Jev)"
NOTE = "Catalog candidates, learned unit frequencies, and Jev picking among the unsure ones. Read from the latest whole-bank run."
KIND = "full"
PATH = SETTINGS["big"]["progress"]
STAMP = "data/em_units.json"
_CACHE = {}


def table():
    if "rows" not in _CACHE:
        path = ROOT / PATH
        fresh = path.exists() and path.stat().st_mtime > (ROOT / STAMP).stat().st_mtime
        rows = json.loads(path.read_text()) if fresh else []
        _CACHE["rows"] = {row["word"]: row for row in rows if row.get("pred") and row.get("category_pred", "word") == "word"}
    return _CACHE["rows"]


def units_for(word, phones):
    row = table().get(word)
    if not row:
        return None
    return normalized([Unit(item["s"], tuple(item["p"])) for item in row["pred"]])


class FREE:
    NAME = "ours-free"
    LABEL = "Our frequencies only (no Jev)"
    NOTE = "The same candidates as our system, picked by learned unit frequencies alone. Free and instant, but it shares its unit list and statistics with our system, so it is not an independent check."
    KIND = "full"

    @staticmethod
    def units_for(word, phones):
        from ..methods import u_em
        result = u_em.run({"word": word, "pron": " ".join(phones), "gold": [], "accepted": []}, None)
        return normalized(result.units)

import json

from ..config import ROOT
from ..models import parse_units
from .common import matches_pron, normalized

NAME = "m2m"
LABEL = "Unsupervised aligner (ours)"
NOTE = "A many-to-many EM aligner trained on the pronunciation dictionary alone, in the style of m2m-aligner. No catalog, no hand labels, no other alignment."
KIND = "full"
PATH = "data/generated/m2m_alignments.json"
_CACHE = {}


def table():
    if "rows" not in _CACHE:
        path = ROOT / PATH
        _CACHE["rows"] = json.loads(path.read_text()) if path.exists() else {}
    return _CACHE["rows"]


def units_for(word, phones):
    text = table().get(word)
    if not text:
        return None
    units = parse_units(text)
    return normalized(units) if matches_pron(units, phones) else None

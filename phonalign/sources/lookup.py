from ..config import SETTINGS
from ..models import parse_units, render_units
from . import REGISTRY
from .common import normalized
from .compare import against, windows

OTHERS = ("production", "phonetisaurus", "m2m", "nettalk")


def preload():
    SETTINGS["alignment"]["scheme"] = "grapheme"
    for name in OTHERS:
        REGISTRY[name].units_for("cat", ["K", "AE", "T"])


def describe(name, word, phones, ours):
    source = REGISTRY[name]
    units = source.units_for(word, phones)
    if not units:
        return {"id": name, "label": source.LABEL, "kind": source.KIND, "align": None}
    relation = against(word, REGISTRY["ours"], ours, source, units)
    diff = windows(ours, units) if relation == "different" and source.KIND == "full" else []
    return {"id": name, "label": source.LABEL, "kind": source.KIND, "align": render_units(units), "relation": relation, "windows": diff}


def answers(word, pron, ours_text):
    phones = pron.split()
    ours = normalized(parse_units(ours_text))
    return [describe(name, word, phones, ours) for name in OTHERS]

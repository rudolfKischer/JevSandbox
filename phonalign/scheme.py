from .config import SETTINGS
from .models import Unit
from .units import R_SOUNDS, splittable


def split_unit(unit):
    sounds = tuple(s.rstrip("012") for s in unit.sounds)
    if len(unit.spelling) < 2 or not splittable(unit.spelling, sounds):
        return [unit]
    if unit.spelling in ("qu", "ks"):
        return [Unit(unit.spelling[0], unit.sounds[:1]), Unit(unit.spelling[1], unit.sounds[1:])]
    cut = unit.spelling.index("r")
    parts = [Unit(unit.spelling[:cut], unit.sounds[:-1]), Unit("r", unit.sounds[-1:])]
    if unit.spelling[cut + 1:]:
        parts.append(Unit(unit.spelling[cut + 1:], ()))
    return parts


def to_grapheme_scheme(units):
    return [part for unit in units for part in split_unit(unit)]


def apply(units):
    return to_grapheme_scheme(units) if SETTINGS["alignment"]["scheme"] == "grapheme" else units

from ..models import Unit, bare
from ..scheme import to_grapheme_scheme


def flat(units):
    return [bare(s) for unit in units for s in unit.sounds]


def matches_pron(units, phones):
    return flat(units) == [bare(p) for p in phones]


SYLLABIC = {"L", "M", "N"}


def merge_schwa(units):
    out = []
    for unit in units:
        if out and unit.sounds and unit.sounds[0] in SYLLABIC and len(unit.sounds) == 1 and out[-1].sounds == ("AH",):
            out[-1] = Unit(out[-1].spelling + unit.spelling, ("AH", unit.sounds[0]))
        else:
            out.append(unit)
    return out


def normalized(units):
    return to_grapheme_scheme([Unit(u.spelling, tuple(bare(s) for s in u.sounds)) for u in units])

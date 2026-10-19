from ..external import nettalk
from ..models import Unit
from .common import normalized

NAME = "nettalk"
LABEL = "NETtalk (hand aligned)"
NOTE = "Twenty thousand words aligned by hand in 1987 for the NETtalk speech network. It marks which letter carries each sound, so only the unit structure is compared, not the sound symbols."
KIND = "structure"


def units_for(word, phones):
    row = nettalk.lookup(word)
    if row is None:
        return None
    units = nettalk.to_units(word, row["marks"])
    return normalized([Unit(u.spelling, tuple("?" for _ in u.sounds)) for u in units])

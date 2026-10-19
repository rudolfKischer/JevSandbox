import json

from .config import ROOT, SETTINGS
from .models import Unit, bare

_TABLE = {}
PIPE = "|"


def table():
    if not _TABLE:
        path = (ROOT / SETTINGS["alignment"]["baseline_source"]).resolve()
        _TABLE.update(json.loads(path.read_text()))
    return _TABLE


def units_for(entry):
    rows = table().get(entry["word"])
    if not rows:
        return None
    units = [Unit(spelling, tuple(sounds.split(PIPE)) if sounds else ()) for spelling, sounds in rows]
    flat = [bare(sound) for unit in units for sound in unit.sounds]
    wanted = [bare(sound) for sound in entry["pron"].split()]
    return units if flat == wanted else None

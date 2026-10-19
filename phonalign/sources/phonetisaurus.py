from .. import baseline
from ..models import Unit
from .common import matches_pron, normalized

NAME = "phonetisaurus"
LABEL = "Phonetisaurus (aligned-cmudict)"
NOTE = "Public alignments of the CMU dictionary made with Phonetisaurus, a statistical many-to-many aligner. Letters are mostly aligned one at a time, so silent letters stand alone."
KIND = "full"


def units_for(word, phones):
    rows = baseline.table().get(word)
    if not rows:
        return None
    units = [Unit(spelling, tuple(sounds.split("|")) if sounds else ()) for spelling, sounds in rows]
    return normalized(units) if matches_pron(units, phones) else None

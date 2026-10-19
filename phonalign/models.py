import re
from dataclasses import dataclass

STRESS = re.compile(r"\d")
SILENT_MARK = "-"
SOUND_JOINER = "+"


@dataclass(frozen=True)
class Unit:
    spelling: str
    sounds: tuple

    @property
    def silent(self):
        return not self.sounds


def bare(sound):
    return STRESS.sub("", sound)


def parse_units(text):
    units = []
    for token in text.split():
        spelling, _, sounds = token.partition(":")
        silent = sounds == SILENT_MARK
        units.append(Unit(spelling, () if silent else tuple(sounds.split(SOUND_JOINER))))
    return units


def render_units(units):
    return " ".join(
        f"{unit.spelling}:{SOUND_JOINER.join(unit.sounds) if unit.sounds else SILENT_MARK}" for unit in units
    )


def canonical(units):
    merged = []
    for unit in units:
        sounds = tuple(bare(sound) for sound in unit.sounds)
        if merged and not sounds and not merged[-1].sounds:
            merged[-1] = Unit(merged[-1].spelling + unit.spelling, ())
        else:
            merged.append(Unit(unit.spelling, sounds))
    return merged


def spans_of(units):
    spans, start = [], 0
    for unit in units:
        spans.append((start, start + len(unit.spelling), unit.sounds))
        start += len(unit.spelling)
    return spans


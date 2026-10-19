from .config import SETTINGS
from .models import Unit, bare
from .tilings import to_units, top_tilings


VOWELS = set("aeiouy")


def shifted(first, second):
    head = first.spelling[:-1]
    if first.spelling in SETTINGS["alignment"]["team_exempt"] or not head or set(head) & VOWELS:
        return False
    return first.spelling[-1] in VOWELS and second.spelling[0] in VOWELS


def doubled(first, second):
    return len(first.spelling) > 1 and second.spelling == first.spelling[-1] and second.spelling not in VOWELS


def gu_split(first, second):
    return first.spelling == "g" and second.spelling[0] == "u" and len(second.spelling) > 1


def team_twin(units, at):
    first, second = units[at], units[at + 1]
    head = Unit(first.spelling[:-1], first.sounds)
    tail = Unit(first.spelling[-1] + second.spelling, second.sounds)
    return units[:at] + [head, tail] + units[at + 2:]


def gu_twin(units, at):
    first, second = units[at], units[at + 1]
    return units[:at] + [Unit("gu", first.sounds), Unit(second.spelling[1:], second.sounds)] + units[at + 2:]


def twins(units):
    for at in range(len(units) - 1):
        first, second = units[at], units[at + 1]
        if shifted(first, second) or doubled(first, second):
            yield tuple(units), tuple(team_twin(units, at))
        elif gu_split(first, second):
            yield tuple(units), tuple(gu_twin(units, at))


def with_teams_intact(pool):
    keys = {tuple(units) for units in pool}
    drop = {worse for units in pool for worse, better in twins(units) if better in keys}
    kept = [units for units in pool if tuple(units) not in drop]
    return kept or pool


STRESSED = ("1", "2")
SYLLABIC_PARTNERS = {"L", "M", "N"}


def stressed_syllabic(units):
    for unit in units:
        if len(unit.sounds) == 2 and bare(unit.sounds[0]) == "AH" and bare(unit.sounds[1]) in SYLLABIC_PARTNERS:
            if unit.sounds[0][-1:] in STRESSED:
                return True
    return False


def without_stressed_syllabics(pool):
    kept = [units for units in pool if not stressed_syllabic(units)]
    return kept or pool


def candidate_pool(entry):
    phones = entry["pron"].split()
    found = top_tilings(entry["word"], phones, SETTINGS["alignment"]["pool_cap"], SETTINGS["alignment"]["pool_slack"])
    pool = with_teams_intact([to_units(entry["word"], phones, tiling) for _, tiling in found])
    return without_stressed_syllabics(pool)


def best_cost(entry):
    found = top_tilings(entry["word"], entry["pron"].split(), 1, 0)
    return found[0][0] if found else None

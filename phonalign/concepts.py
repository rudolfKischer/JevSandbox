from .models import bare

VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
VOWEL_LETTERS = set("aeiouy")


def vowel_unit(unit):
    return bool(unit.sounds) and bare(unit.sounds[0]) in VOWELS


def consonant_unit(unit):
    return bool(unit.sounds) and all(bare(s) not in VOWELS for s in unit.sounds)


def r_controlled(units):
    found = []
    for index, unit in enumerate(units):
        after_vowel = index > 0 and vowel_unit(units[index - 1]) and bare(unit.sounds[0] if unit.sounds else "") == "R"
        if after_vowel:
            found.append(units[index - 1].spelling + unit.spelling)
        elif unit.sounds and bare(unit.sounds[0]) == "ER" and len(unit.sounds) == 1 and "r" in unit.spelling:
            found.append(unit.spelling)
    return found


def blends(units):
    found, run = [], []
    for unit in units + [None]:
        if unit is not None and consonant_unit(unit) and len(unit.sounds) == 1:
            run.append(unit.spelling)
            continue
        if len(run) >= 2:
            found.append("".join(run))
        run = []
    return found


def silent_e(units):
    if len(units) < 3 or units[-1].spelling != "e" or units[-1].sounds:
        return []
    if consonant_unit(units[-2]) and vowel_unit(units[-3]):
        return [units[-3].spelling + units[-2].spelling + "e"]
    return []


def pure_vowel(unit):
    return vowel_unit(unit) and all(bare(s) in VOWELS or bare(s) == "Y" for s in unit.sounds)


def by_length(units, wanted, check):
    return [u.spelling for u in units if len(u.spelling) == wanted and check(u) and u.spelling[0] != u.spelling[-1]]


def detect(units):
    flags = {
        "r-controlled": r_controlled(units),
        "blend": blends(units),
        "silent e": silent_e(units),
        "consonant digraph": by_length(units, 2, lambda u: consonant_unit(u) and len(u.sounds) == 1),
        "vowel team": [u.spelling for u in units if len(u.spelling) >= 2 and pure_vowel(u) and not u.spelling.endswith("r")],
        "double consonant": [u.spelling for u in units if len(u.spelling) == 2 and u.spelling[0] == u.spelling[1] and u.sounds],
        "silent letter": [u.spelling for u in units if not u.sounds and u.spelling != "e"],
    }
    return {name: items for name, items in flags.items() if items}

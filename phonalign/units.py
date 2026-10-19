import json
from collections import defaultdict

from . import catalog
from .config import SETTINGS, root_path
from .models import bare

_CACHE = {}
SYLLABIC = "suffix_cle"
SYLLABIC_SOUNDS = ("AH", "L")
R_SOUNDS = ("R", "ER")
QU = ("qu", ("K", "W"))
SPLIT_PAIRS = {QU, ("ks", ("K", "S"))}


def splittable(spelling, option):
    if len(option) < 2:
        return False
    return option[-1] in R_SOUNDS or (spelling, tuple(option)) in SPLIT_PAIRS


SYLLABIC_L = {"al", "el", "il", "ol", "ul"}
INFLECTIONS = {"", "s", "es", "d", "ed", "ly", "y", "ing"}


def table():
    if "table" not in _CACHE:
        sounds = json.loads(root_path("data/og_sounds.json").read_text())
        known = defaultdict(lambda: defaultdict(set))
        for item in catalog.entries():
            spelling, position = item["grapheme"], item.get("position", "any")
            for option in options_for(item, sounds):
                if SETTINGS["alignment"]["scheme"] == "grapheme" and splittable(spelling, option):
                    continue
                known[spelling][tuple(option)].add(position)
        derive_parts(known, sounds)
        add_extra(known)
        if SETTINGS["alignment"]["dialect"] == "uk":
            add_non_rhotic(known)
        _CACHE["table"] = known
    return _CACHE["table"]


def add_non_rhotic(known):
    from .dialect import rules
    for spelling in list(known):
        for option in list(known[spelling]):
            variant = tuple(rules.non_rhotic(list(option)))
            if variant and variant != option:
                known[spelling][variant] |= known[spelling][option]


SYLLABIC_LETTERS = {"m": ("AH", "M"), "n": ("AH", "N"), "l": ("AH", "L")}
VOWEL_LETTERS = set("aeiouy")


def syllabic_option(word, i, j):
    if not SETTINGS["alignment"].get("syllabic_units") or j - i != 1 or word[i] not in SYLLABIC_LETTERS:
        return None
    if i == 0 or word[i - 1] in VOWEL_LETTERS:
        return None
    return SYLLABIC_LETTERS[word[i]]


def add_extra(known):
    for item in json.loads(root_path(SETTINGS["alignment"]["extra_units"]).read_text())["units"]:
        known[item["spelling"]][tuple(item["sounds"])].add("any")


def cross_type(letter, sounds):
    alignment = SETTINGS["alignment"]
    return letter in alignment["consonant_letters"] and any(sound in alignment["vowel_sounds"] for sound in sounds)


def derive_parts(known, sounds):
    if SETTINGS["alignment"]["scheme"] != "grapheme":
        return
    for item in catalog.entries():
        for option in options_for(item, sounds):
            spelling = item["grapheme"]
            if not splittable(spelling, option):
                continue
            if option[-1] in R_SOUNDS and "r" in spelling:
                cut = spelling.index("r")
                known["r"][(option[-1],)].add("any")
                if cut and len(option) > 1:
                    known[spelling[:cut]][tuple(option[:-1])].add("any")
            elif (spelling, tuple(option)) == QU:
                known["u"][("W",)].add("any")


def options_for(item, sounds):
    spelling = item["grapheme"]
    if item["category"] == SYLLABIC or spelling == "le" or (spelling in SYLLABIC_L and item["phoneme_id"] == "l"):
        return [SYLLABIC_SOUNDS]
    return sounds.get(item["phoneme_id"], [])




def compatible(spelling, sounds):
    return tuple(bare(s) for s in sounds) in table().get(spelling, {})


def units_with(spelling):
    return table().get(spelling, {})

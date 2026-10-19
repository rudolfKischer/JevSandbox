from ..models import bare
from .common import merge_schwa

IDENTICAL = "identical"
STRUCTURE = "structure"
DIFFERENT = "different"


def sounding(units):
    out, start, silent = [], 0, set()
    for unit in units:
        end = start + len(unit.spelling)
        if unit.sounds:
            out.append((start, end, tuple(bare(s) for s in unit.sounds)))
        else:
            silent.update(range(start, end))
        start = end
    return out, silent


def letters(span):
    return set(range(span[0], span[1]))


def same_structure(a, b, with_sounds):
    (spans_a, silent_a), (spans_b, silent_b) = sounding(a), sounding(b)
    if len(spans_a) != len(spans_b):
        return False
    for x, y in zip(spans_a, spans_b):
        if with_sounds and x[2] != y[2]:
            return False
        extra_a, extra_b = letters(x) - letters(y), letters(y) - letters(x)
        if not extra_a <= silent_b or not extra_b <= silent_a:
            return False
    return True


def key(units):
    return tuple((u.spelling, tuple(bare(s) for s in u.sounds)) for u in units)


def relation(a, b, with_sounds=True):
    a, b = merge_schwa(a), merge_schwa(b)
    if with_sounds and key(a) == key(b):
        return IDENTICAL
    return STRUCTURE if same_structure(a, b, with_sounds) else DIFFERENT


def split_syllabic(units):
    from ..models import Unit
    out = []
    for unit in units:
        if len(unit.spelling) > 1 and unit.sounds[:1] == ("AH",) and len(unit.sounds) == 2 and unit.sounds[1] in ("L", "M", "N"):
            out += [Unit(unit.spelling[:-1], unit.sounds[:1]), Unit(unit.spelling[-1], unit.sounds[1:])]
        else:
            out.append(unit)
    return out


def against(word, a, a_units, b, b_units):
    from ..external import check
    full_a, full_b = a.KIND == "full", b.KIND == "full"
    if full_a and full_b:
        return relation(a_units, b_units, True)
    if full_a != full_b:
        ok = check.structure_ok(word, split_syllabic(a_units if full_a else b_units))
        return None if ok is None else (STRUCTURE if ok else DIFFERENT)
    return relation(a_units, b_units, False)


def ends(units):
    out, position = {0}, 0
    for unit in units:
        position += len(unit.spelling)
        out.add(position)
    return out


def slice_units(units, start, stop):
    out, position = [], 0
    for unit in units:
        if start <= position < stop:
            out.append(unit)
        position += len(unit.spelling)
    return out


def text_of(units):
    return " ".join(f"{u.spelling}:{'+'.join(bare(s) for s in u.sounds) or '-'}" for u in units)


def windows(a, b):
    a, b = merge_schwa(a), merge_schwa(b)
    common = sorted(ends(a) & ends(b))
    found = []
    for start, stop in zip(common, common[1:]):
        left, right = slice_units(a, start, stop), slice_units(b, start, stop)
        if key(left) != key(right):
            found.append(f"{text_of(left)} \u2192 {text_of(right)}")
    return found

from . import nettalk

SYLLABIC = set("LMN")


def structure_ok(word, units):
    row = nettalk.lookup(word)
    if row is None or sum(len(u.spelling) for u in units) != len(word) or SYLLABIC & set(row["marks"]):
        return None
    found = {i for i, _ in nettalk.bearers(word, row["marks"])}
    start = 0
    for unit in units:
        count = sum(start <= i < start + len(unit.spelling) for i in found)
        if count != (1 if unit.sounds else 0):
            return False
        start += len(unit.spelling)
    return True

import json
from collections import defaultdict

from .config import PROMPTS, ROOT, SETTINGS

_CACHE = {}
EXAMPLES_SHOWN = 3
SPLIT_MARK = "_"


def entries():
    if "rows" not in _CACHE:
        path = (ROOT / SETTINGS["alignment"]["catalog_source"]).resolve()
        _CACHE["rows"] = json.loads(path.read_text())
    return _CACHE["rows"]


def spellings():
    return {item["grapheme"] for item in entries()}




def by_category():
    groups = defaultdict(lambda: defaultdict(list))
    for item in entries():
        if SPLIT_MARK not in item["grapheme"]:
            groups[item["category"]][item["grapheme"]].extend(item["examples"])
    return groups


def state_block():
    block = {}
    for category, items in by_category().items():
        label = PROMPTS["catalog_labels"].get(category, category)
        block[label] = [f"{g} ({next(iter(dict.fromkeys(ex)), '')})" for g, ex in items.items()]
    return block




def note_for(spelling):
    for item in entries():
        if item["grapheme"] == spelling and item["examples"]:
            label = PROMPTS["unit_labels"].get(item["category"], item["category"])
            return f"{spelling} ({label}, as in {item['examples'][0]})"
    return None

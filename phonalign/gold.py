import json

from .config import SETTINGS, root_path
from . import catalog, scheme
from .models import canonical, parse_units, spans_of


def judged_for(part):
    path = root_path("data/samples") / f"{part}-judged.json"
    return json.loads(path.read_text())["words"] if path.exists() else {}


def load_gold(name="starter"):
    entries = []
    for part in name.split("+"):
        path = root_path(SETTINGS["alignment"]["gold_dir"]) / f"{part}.json"
        if not path.exists():
            path = root_path("data/samples") / f"{part}.json"
        loaded = json.loads(path.read_text())
        verdicts = judged_for(part) if loaded.get("judged") else {}
        for entry in loaded["words"]:
            entry["unlabeled"] = bool(loaded.get("unlabeled")) and not verdicts
            if entry["word"] in verdicts:
                entry["judge"] = verdicts[entry["word"]]
        entries.extend(loaded["words"])
    for entry in entries:
        entry.setdefault("category", "word")
        entry["gold"] = scheme.apply(parse_units(entry["units"])) if "units" in entry else []
        entry["accepted"] = [scheme.apply(parse_units(text)) for text in entry.get("accept", [])]
        entry["gap"] = sorted({u.spelling for u in entry["gold"] if len(u.spelling) > 1 and u.sounds and u.spelling not in catalog.spellings()})
    return entries


def is_exact(predicted, entry):
    options = [entry["gold"]] + entry["accepted"]
    return canonical(predicted) in [canonical(option) for option in options]


def unit_hits(predicted, entry):
    if not entry["gold"]:
        return 1.0
    best = 0
    for option in [entry["gold"]] + entry["accepted"]:
        wanted = set(spans_of(canonical(option)))
        found = set(spans_of(canonical(predicted)))
        best = max(best, len(wanted & found) / len(wanted))
    return best


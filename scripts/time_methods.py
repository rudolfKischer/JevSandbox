import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from phonalign.config import SETTINGS
from phonalign.gold import load_gold
from phonalign.methods import REGISTRY
from phonalign.runner import run_batched, run_entry
from rerun_all import flags

SAMPLE = 12
SKIP = {"senses", "kinds", "baseline"}


def apply(config):
    for key in ("notation", "silent_weight", "rules", "examples", "catalog_in_state", "scheme", "wording", "unit_notes", "gate_router"):
        if key in config:
            SETTINGS["alignment"][key] = config[key]


def measure(data):
    apply(data["config"])
    SETTINGS["workers"] = 1
    entries = [e for e in load_gold(data["gold"]) if e["category"] == "word" or data["method"] == "r"]
    sample = entries[:: max(len(entries) // SAMPLE, 1)][:SAMPLE]
    live = data.get("live", True) and data["method"] != "p"
    SETTINGS["no_cache"] = live
    if data.get("batch") and live:
        rows = run_batched(sample[: data["batch"]] if len(sample) >= data["batch"] else load_gold(data["gold"])[: data["batch"]], data["method"], data["experiment"], data["batch"])
        seconds = sum(r.get("latency", 0) for r in rows) / len(rows)
        return {"sample": len(rows), "seconds_per_word": round(seconds, 5), "requests_per_word": round(sum(r.get("calls", 0) for r in rows) / len(rows), 3)}
    started = time.time()
    rows = [run_entry(entry, data["method"], data["experiment"] if live else None) if live else run_entry(entry, data["method"], "timing-free") for entry in sample]
    wall = time.time() - started
    seconds = sum(r.get("latency", 0) for r in rows) / len(rows) if live else wall / len(rows)
    return {"sample": len(rows), "seconds_per_word": round(seconds, 4), "requests_per_word": round(sum(r.get("calls", 0) for r in rows) / len(rows), 2)}


def main():
    only = set(sys.argv[1:])
    for path in sorted((ROOT / "results").glob("*.json")):
        data = json.loads(path.read_text())
        if data["method"] in SKIP or data["method"] not in REGISTRY or (only and data["experiment"] not in only):
            continue
        timing = measure(data)
        data["summary"]["timing"] = timing
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print(data["experiment"], timing)


if __name__ == "__main__":
    main()

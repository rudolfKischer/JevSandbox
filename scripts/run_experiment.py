import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS
from phonalign.gold import load_gold
from phonalign.methods import REGISTRY
from phonalign.runner import run, summarize


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--method", choices=["baseline", *REGISTRY], default="q")
    parser.add_argument("--gold", default="starter+edge+special")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", help="comma separated gold ids")
    parser.add_argument("--notation", choices=["ipa", "arpabet", "both"])
    parser.add_argument("--silent-weight", type=float)
    parser.add_argument("--scheme", choices=["teaching", "grapheme"], help="grapheme splits vowel+r and qu into separate units")
    parser.add_argument("--wording", choices=["literal", "unit"], help="how the per-sound question is phrased")
    parser.add_argument("--no-gate", action="store_true", help="ask the kind question for every word")
    parser.add_argument("--notes", action="store_true", help="add short notes about the units that differ between candidates")
    parser.add_argument("--catalog", action="store_true", help="put the unit catalog in the state")
    parser.add_argument("--examples", action="store_true", help="put worked examples in the state")
    parser.add_argument("--no-rules", action="store_true", help="leave the spelling rules out of the state")
    parser.add_argument("--batch", type=int, default=0, help="words per request for methods that support it")
    parser.add_argument("--live", action="store_true", help="make real API calls (default is a dry run)")
    return parser.parse_args()


def pick(entries, args):
    entries = [entry for entry in entries if args.method == "r" or entry["category"] == "word"]
    if args.ids:
        wanted = set(args.ids.split(","))
        entries = [entry for entry in entries if entry["id"] in wanted]
    return entries[: args.limit] if args.limit else entries


def apply_overrides(args):
    if args.notation:
        SETTINGS["alignment"]["notation"] = args.notation
    if args.scheme:
        SETTINGS["alignment"]["scheme"] = args.scheme
    if args.wording:
        SETTINGS["alignment"]["wording"] = args.wording
    if args.no_gate:
        SETTINGS["alignment"]["gate_router"] = False
    if args.notes:
        SETTINGS["alignment"]["unit_notes"] = True
    if args.catalog:
        SETTINGS["alignment"]["catalog_in_state"] = True
    if args.examples:
        SETTINGS["alignment"]["examples"] = True
    if args.no_rules:
        SETTINGS["alignment"]["rules"] = False
    if args.silent_weight is not None:
        SETTINGS["alignment"]["silent_weight"] = args.silent_weight


def save(args, rows, started):
    target = ROOT / SETTINGS["alignment"]["results_dir"] / f"{args.name}.json"
    keys = ("notation", "silent_weight", "max_span_letters", "rules", "examples", "catalog_in_state", "wording", "scheme", "unit_notes", "gate_router")
    config = {key: SETTINGS["alignment"][key] for key in keys}
    live = args.live or args.method == "baseline"
    payload = {
        "experiment": args.name, "method": args.method, "live": live, "gold": args.gold, "batch": args.batch,
        "created": time.strftime("%Y-%m-%d %H:%M"), "model": SETTINGS["model"], "config": config,
        "summary": summarize(rows, started), "words": rows,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(payload["summary"], indent=1), f"\n-> {target.relative_to(ROOT)}")


def main():
    args = parse()
    apply_overrides(args)
    started = time.time()
    entries = pick(load_gold(args.gold), args)
    label = args.name if (args.live or args.method == "baseline") else None
    save(args, run(entries, args.method, label, args.batch), started)


if __name__ == "__main__":
    main()

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import runner
from phonalign.progress import Bar
from phonalign.config import SETTINGS
from phonalign.gold import load_gold
from phonalign.methods import REGISTRY
from phonalign.models import Unit, canonical, spans_of

BIG = SETTINGS["big"]
FREE = ("p", "u")
DROP = ("detail", "nettalk", "gold", "accept")


def spans(units):
    return [(a, b) for a, b, _ in spans_of(canonical(units))]


def free_agreement(entry, pred_units):
    out = {}
    for name in FREE:
        other = REGISTRY[name].run(entry, None).units
        out[f"{name}_same"] = spans(other) == spans(pred_units)
    return out


def slim(row, entry, units):
    row.update(free_agreement(entry, units))
    for key in DROP:
        row.pop(key, None)
    row["gold"], row["accept"] = [], []
    return row


def flags(row):
    return [row.get("nettalk_ok") is False, row.get("baseline_same") is False, row.get("p_same") is False, row.get("u_same") is False]


def run_block(block, label):
    rows = runner.run(block, BIG["method"], label, BIG["batch"])
    by_word = {entry["id"]: entry for entry in block}
    out = []
    for row in rows:
        units = [runner_unit(item) for item in row["pred"]] if "pred" in row else None
        out.append(slim(row, by_word[row["id"]], units) if units else row)
    return out


def runner_unit(item):
    return Unit(item["s"], tuple(item["p"]))


def bucket_table(rows):
    table = {}
    for row in rows:
        bucket = (row["tags"] or ["rest"])[0]
        table.setdefault(bucket, []).append(row)
    return {name: bucket_summary(items) for name, items in table.items()}


def bucket_summary(items):
    out = {"words": len(items)}
    for key in ("nettalk_ok", "baseline_same", "p_same", "u_same"):
        known = [r for r in items if r.get(key) is not None]
        out[key] = round(sum(bool(r[key]) for r in known) / max(len(known), 1), 4) if known else None
        out[key + "_n"] = len(known)
    out["cost_usd"] = round(sum(r.get("cost", 0) for r in items), 4)
    return out


def choose(rows):
    flagged = sorted((r for r in rows if any(flags(r))), key=lambda r: -sum(flags(r)))
    kept = flagged[: BIG["keep_flagged"]]
    calm = [r for r in rows if not any(flags(r))]
    step = max(len(calm) // BIG["keep_agreeing"], 1)
    return kept + calm[::step][: BIG["keep_agreeing"]], len(flagged)


def save(name, rows, started, method):
    summary = runner.summarize(rows, started)
    kept, flagged = choose(rows)
    summary.update(flagged=flagged, buckets=bucket_table(rows), rows_kept=len(kept))
    for key in ("baseline_same", "p_same", "u_same"):
        known = [r for r in rows if r.get(key) is not None]
        summary[key.replace("_same", "_agree")] = runner.rate(known, key) if known else None
    config = {k: SETTINGS["alignment"][k] for k in ("notation", "rules", "catalog_in_state", "scheme", "gate_router", "em_skip")}
    payload = {"experiment": name, "method": method, "live": True, "gold": BIG["name"], "batch": BIG["batch"], "partial": True,
               "total_words": len(rows), "created": time.strftime("%Y-%m-%d %H:%M"), "model": SETTINGS["model"], "config": config,
               "summary": summary, "words": kept}
    target = ROOT / SETTINGS["alignment"]["results_dir"] / f"{name}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=1), "->", target.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?", default="bank-route")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    SETTINGS["alignment"]["scheme"] = BIG["scheme"]
    SETTINGS["alignment"]["catalog_in_state"] = True
    entries = load_gold(BIG["name"])[: args.limit] if args.limit else load_gold(BIG["name"])
    started, rows = time.time(), []
    bar = Bar(len(entries), args.name)
    for start in range(0, len(entries), BIG["block"]):
        block = run_block(entries[start:start + BIG["block"]], args.name if args.live else None)
        rows += block
        bar.update(len(block), f"${sum(r.get('cost', 0) for r in rows):.3f}")
    bar.close()
    (ROOT / BIG["progress"]).write_text(json.dumps(rows, ensure_ascii=False))
    save(args.name, rows, started, BIG["method"])


if __name__ == "__main__":
    main()

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS
from phonalign.progress import Bar
from phonalign.pron import espeak, unitg2p
from phonalign.pron.runner import bare_list, distance, load_set, wiki_variants

BIG = SETTINGS["big"]
SOURCES = ("espeak", "wikipron", "unit")


def predictions(item):
    variants = wiki_variants(item["word"])
    return {
        "espeak": espeak.generate(item["word"]) or [],
        "wikipron": variants[0] if variants else None,
        "unit": (unitg2p.generate(item["word"], 1) or [[]])[0],
        "variants": variants,
    }


def judge(item):
    truth = bare_list(item["truth"][0]) if isinstance(item["truth"], list) else bare_list(item["truth"])
    found = predictions(item)
    row = {"id": item["id"], "word": item["word"], "tags": item["tags"], "truth": truth}
    for name in SOURCES:
        guess = found[name]
        row[name] = guess
        row[name + "_ok"] = None if guess is None else guess == truth
        row[name + "_edit"] = None if guess is None else distance(guess, truth)
    row["variants"] = found["variants"][:4]
    row["wiki_any_ok"] = any(v == truth for v in found["variants"]) if found["variants"] else None
    row["pair"] = None if not found["variants"] else found["espeak"] in found["variants"]
    return row


def rate(rows, key):
    known = [r for r in rows if r[key] is not None]
    return {"n": len(known), "rate": round(sum(bool(r[key]) for r in known) / max(len(known), 1), 4)}


def method_row(row, name):
    guess = row[name]
    out = {"id": row["id"], "word": row["word"], "sense": None, "tags": row["tags"], "pred": guess, "truth": [row["truth"]],
           "exact": bool(row[name + "_ok"]), "edit": row[name + "_edit"], "phones": len(row["truth"]), "seconds": 0}
    if name == "espeak":
        out["flag"] = "unchecked" if row["pair"] is None else ("agree" if row["pair"] else "disagree")
        out["candidates"] = [{"pron": v, "source": "WikiPron", "p": 0} for v in row["variants"]]
    return out


def keep(rows):
    wrong = [r for r in rows if not r["exact"]]
    right = [r for r in rows if r["exact"]]
    return wrong[: BIG["keep_flagged"]] + right[:: max(len(right) // BIG["keep_agreeing"], 1)][: BIG["keep_agreeing"]]


def run_summary(rows, started, covered):
    n = max(len(rows), 1)
    out = {"words": len(rows), "exact": sum(r["exact"] for r in rows), "exact_rate": round(sum(r["exact"] for r in rows) / n, 4),
           "within_one": round(sum(r["edit"] <= 1 for r in rows) / n, 4),
           "phone_error": round(sum(r["edit"] for r in rows) / max(sum(r["phones"] for r in rows), 1), 4),
           "per_thousand": 0.0, "seconds_per_word": round((time.time() - started) / n, 5), "covered": covered}
    return out


def checked_summary(all_rows):
    agreed = [r for r in all_rows if r["pair"]]
    rest = [r for r in all_rows if not r["pair"]]
    return {"accepted_rate": round(len(agreed) / len(all_rows), 4), "accepted_exact": rate(agreed, "espeak_ok")["rate"], "rest_exact": rate(rest, "espeak_ok")["rate"]}


def bucket_table(all_rows):
    out = {}
    for tag in sorted({r["tags"][0] for r in all_rows}):
        part = [r for r in all_rows if r["tags"][0] == tag]
        agreed = [r for r in part if r["pair"]]
        out[tag] = {"words": len(part), "espeak": rate(part, "espeak_ok")["rate"], "wikipron": rate(part, "wikipron_ok")["rate"], "unit": rate(part, "unit_ok")["rate"],
                    "accepted": round(len(agreed) / len(part), 4), "accepted_exact": rate(agreed, "espeak_ok")["rate"]}
    return out


def save(name, method, rows, summary):
    payload = {"experiment": name, "method": method, "set": BIG["name"], "partial": True, "total_words": summary["words"],
               "created": time.strftime("%Y-%m-%d %H:%M"), "summary": summary, "words": keep(rows)}
    (ROOT / "results" / "pron" / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")


def write_all(all_rows, started):
    buckets, checked = bucket_table(all_rows), checked_summary(all_rows)
    plans = {"espeak": all_rows, "wikipron": [r for r in all_rows if r["wikipron"] is not None], "unit": all_rows}
    for name, source in plans.items():
        rows = [method_row(r, name) for r in source]
        summary = run_summary(rows, started, round(len(source) / len(all_rows), 4))
        summary["buckets"] = buckets
        save(f"pron-{name}-{BIG['name']}", name, rows, summary)
    rows = [method_row(r, "espeak") for r in all_rows]
    summary = run_summary(rows, started, 1.0) | checked
    summary["buckets"] = buckets
    save(f"pron-checked-{BIG['name']}", "checked", rows, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "buckets"}, indent=1))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    items = load_set(BIG["name"])[:limit]
    started = time.time()
    bar, rows = Bar(len(items), "pron-bank"), []
    with ThreadPoolExecutor(8) as pool:
        for row in pool.map(judge, items):
            rows.append(row)
            bar.update(1)
    bar.close()
    write_all(rows, started)


if __name__ == "__main__":
    main()

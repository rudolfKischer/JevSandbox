import time
from concurrent.futures import ThreadPoolExecutor

from . import baseline, concepts, scheme
from .external import check, nettalk
from .caller import Caller, DryRun
from .config import SETTINGS
from .gold import is_exact, unit_hits
from .models import render_units
from .methods import REGISTRY


def unit_json(unit):
    return {"s": unit.spelling, "p": list(unit.sounds)}


def spans_only(units):
    from .models import canonical, spans_of
    return [(a, b) for a, b, _ in spans_of(canonical(units))]


def baseline_same(entry, units):
    other = baseline.units_for(entry)
    if other is None or "".join(u.spelling for u in other) != entry["word"]:
        return None
    return spans_only(scheme.apply(other)) == spans_only(units)


def unit_json_list(units):
    return [unit_json(u) for u in units]


def base_row(entry):
    return {
        "id": entry["id"], "word": entry["word"], "pron": entry["pron"], "tags": entry.get("tags", []),
        "sense": entry.get("sense"), "dialect": entry.get("dialect"), "category": entry["category"], "review": entry.get("review"), "silver": entry.get("silver"), "unlabeled": entry.get("unlabeled"),
        "gold": [unit_json(u) for u in entry["gold"]], "gap": entry["gap"],
        "accept": [[unit_json(u) for u in option] for option in entry["accepted"]],
    }


UNREAD = {"verdict": "unread", "pattern": "", "note": "differs from the answer I judged; not read yet"}


def verdict_for(entry, units):
    judge = entry["judge"]
    text = render_units(units)
    if text == judge.get("units"):
        return judge
    return judge.get("alts", {}).get(text)


def fill_judged(row, entry, units):
    found = verdict_for(entry, units)
    row["unit_hits"] = None
    if found is None:
        row["exact"], row["unread"] = False, True
        row["judge"] = UNREAD
        return
    row["exact"] = found["verdict"] == "ok"
    row["judge"] = found
    row["tags"] = row["tags"] + ([found["pattern"]] if found.get("pattern") else [])


def fill(row, entry, result):
    row["pred"] = [unit_json(u) for u in result.units]
    category = result.extra.get("category")
    if entry.get("judge"):
        fill_judged(row, entry, result.units)
    elif entry.get("unlabeled"):
        row["exact"], row["unit_hits"] = None, None
        if entry.get("silver") and category is not None:
            row["silver_ok"] = category == entry["silver"]
    else:
        row["exact"] = is_exact(result.units, entry) if category is None else (category == entry["category"] and (not entry["gold"] or is_exact(result.units, entry)))
        row["unit_hits"] = round(unit_hits(result.units, entry), 4)
    if entry["category"] == "word" and result.units:
        row["concepts"] = concepts.detect(result.units)
        row["nettalk_ok"] = check.structure_ok(entry["word"], result.units)
        if entry.get("unlabeled") and not entry.get("judge"):
            row["baseline_same"] = baseline_same(entry, result.units)
        found = nettalk.lookup(entry["word"])
        if found:
            row["nettalk"] = unit_json_list(nettalk.to_units(entry["word"], found["marks"]))
    if result.posterior is not None:
        row["posterior"] = round(result.posterior, 4)
    for item, confidence in zip(row["pred"], result.confidences or []):
        item["c"] = confidence
    row["detail"] = {"rows": result.rows}
    extra = dict(result.extra)
    if "category" in extra:
        row["category_pred"] = extra.pop("category")
    row.update(extra)


def stats(row, call, share=1):
    row.update(questions=round(call.questions / share, 2), calls=round(call.calls / share, 2), tokens_estimate=round(call.estimate / share))
    if call.timed and call.calls:
        row["latency"] = round(call.elapsed / share, 3)


def finish(row, entry, result, call, share=1):
    stats(row, call, share)
    if result is None:
        row["unavailable"] = True
        return row
    fill(row, entry, result)
    row.update(tokens=round(call.tokens / share), cost=call.cost / share)
    return row


def run_entry(entry, method, label):
    row = base_row(entry)
    if method == "baseline":
        units = baseline.units_for(entry)
        if units is None:
            row["unavailable"] = True
        else:
            from .result import Result
            fill(row, entry, Result(units))
        return row
    call = Caller(label)
    try:
        result = REGISTRY[method].run(entry, call)
    except DryRun:
        stats(row, call)
        row["unavailable"] = label is not None
        return row
    return finish(row, entry, result, call)


def run_chunk(chunk, method, label):
    call = Caller(label)
    try:
        results = REGISTRY[method].run_batch(chunk, call)
    except DryRun:
        return [dict(base_row(entry), unavailable=False, questions=0) for entry in chunk]
    return [finish(base_row(entry), entry, result, call, len(chunk)) for entry, result in zip(chunk, results)]


def run_batched(entries, method, label, size):
    chunks = [entries[i:i + size] for i in range(0, len(entries), size)]
    with ThreadPoolExecutor(SETTINGS["workers"] if label else 1) as pool:
        return [row for rows in pool.map(lambda c: run_chunk(c, method, label), chunks) for row in rows]


CONFIDENT = 0.7


def auc(rows):
    good = [r["posterior"] for r in rows if r["exact"]]
    bad = [r["posterior"] for r in rows if not r["exact"]]
    if not good or not bad:
        return None
    wins = sum((g > b) + 0.5 * (g == b) for g in good for b in bad)
    return round(wins / (len(good) * len(bad)), 4)


def rate(rows, key):
    return round(sum(bool(row[key]) for row in rows) / max(len(rows), 1), 4)


def summarize(rows, started):
    scored = [row for row in rows if "pred" in row]
    labeled = [row for row in scored if row["exact"] is not None]
    rated = [row for row in scored if "posterior" in row]
    cost = round(sum(r.get("cost", 0) for r in rows), 6)
    count = max(len(labeled), 1)
    summary = {
        "per_thousand": round(cost / max(len(rows), 1) * 1000, 4), "words": len(rows), "scored": len(scored),
        "exact": sum(r["exact"] for r in labeled), "exact_rate": rate(labeled, "exact") if labeled else None,
        "unit_rate": round(sum(r["unit_hits"] for r in labeled) / count, 4) if labeled and labeled[0]["unit_hits"] is not None else None,
        "questions": sum(r.get("questions", 0) for r in rows),
        "tokens": sum(r.get("tokens", r.get("tokens_estimate", 0)) for r in rows),
        "cost_usd": cost, "mean_posterior": round(sum(r["posterior"] for r in rated) / max(len(rated), 1), 4),
        "auc": auc(rated) if labeled else None, "seconds": round(time.time() - started, 1),
    }
    known = [r for r in scored if r.get("nettalk_ok") is not None]
    if known:
        summary["nettalk_agree"] = rate(known, "nettalk_ok")
    if not labeled and rated:
        summary["confident_rate"] = round(sum(r["posterior"] >= CONFIDENT for r in rated) / len(rated), 4)
        summary["no_tiling"] = sum(bool(r.get("no_tiling")) for r in scored)
    silver = [r for r in scored if "silver_ok" in r]
    if silver:
        summary["silver_agree"] = rate(silver, "silver_ok")
    unread = sum(bool(r.get("unread")) for r in scored)
    if unread:
        summary["unread"] = unread
    judged = [r for r in scored if r.get("judge")]
    if judged:
        summary["wrong"] = sum(r["judge"]["verdict"] == "wrong" for r in judged)
        summary["doubtful"] = sum(r["judge"]["verdict"] == "doubtful" for r in judged)
    if any("oracle" in r for r in labeled):
        summary["oracle_rate"] = rate([r for r in labeled if "oracle" in r], "oracle")
    return summary


def run(entries, method, label, batch=0):
    if batch and hasattr(REGISTRY.get(method), "run_batch"):
        return run_batched(entries, method, label, batch)
    workers = SETTINGS["workers"] if label else 1
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda entry: run_entry(entry, method, label), entries))

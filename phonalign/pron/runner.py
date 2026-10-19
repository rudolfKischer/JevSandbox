import json
import time

from ..caller import Caller
from ..config import root_path
from ..models import bare
from . import espeak, pick, unitg2p
from ..dialect import ipa
from ..config import ROOT

_WIKI = {}


def wikipron():
    if not _WIKI:
        _WIKI.update(ipa.load_wikipron(ROOT / "data" / "external" / "wikipron" / "eng_us.tsv"))
    return _WIKI


def wiki_variants(word):
    return [list(v) for v in sorted(wikipron().get(word, []))]

BATCH = 100
POOL_UNIT_CANDIDATES = 4
POOL_CAP = 6


def load_set(name):
    return json.loads(root_path(f"data/pron/{name}.json").read_text())["words"]


def bare_list(text):
    return [bare(p) for p in text.split()]


def truths(item):
    return [bare_list(v) for v in item["truth"]]


def distance(a, b):
    row = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, row[0] = row[0], i
        for j in range(1, len(b) + 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
    return row[-1]


def pool_for(item):
    if item.get("candidates"):
        return [(bare_list(c), "dictionary") for c in item["candidates"]]
    pool, seen = [], set()
    guesses = [(espeak.generate(item["word"]) or [], "espeak")]
    guesses += [(g, "unit statistics") for g in unitg2p.generate(item["word"], POOL_UNIT_CANDIDATES)]
    for phones, source in guesses:
        if phones and tuple(phones) not in seen:
            seen.add(tuple(phones))
            pool.append((phones, source))
    return pool[:POOL_CAP]


def score(row, item):
    options = truths(item)
    best = min(distance(row["pred"], t) for t in options)
    row.update(exact=best == 0, edit=best, phones=min(len(t) for t in options), truth=options)
    return row


def base_row(item):
    return {"id": item["id"], "word": item["word"], "sense": item.get("sense"), "tags": item.get("tags", [])}


def run_code(item, produce):
    started = time.time()
    row = base_row(item)
    row["pred"] = produce(item) or []
    row["seconds"] = time.time() - started
    return score(row, item)


def run_checked(item):
    started = time.time()
    row = base_row(item)
    row["pred"] = espeak.generate(item["word"]) or []
    variants = wiki_variants(item["word"])
    row["flag"] = "unchecked" if not variants else ("agree" if row["pred"] in variants else "disagree")
    row["candidates"] = [{"pron": v, "source": "WikiPron", "p": 0} for v in variants[:4]]
    row["seconds"] = time.time() - started
    return score(row, item)


def run_pick(items, label, use_hints):
    pools = [pool_for(it) for it in items]
    call = Caller(label)
    started = time.time()
    shares = []
    for start in range(0, len(items), BATCH):
        chunk_items, chunk_pools = items[start:start + BATCH], pools[start:start + BATCH]
        shares += pick.jev_batch(chunk_items, [[p for p, _ in pool] for pool in chunk_pools], call, use_hints)
    elapsed = call.elapsed
    rows = []
    for item, pool, share in zip(items, pools, shares):
        row = base_row(item)
        best = max(range(len(pool)), key=lambda i: share[i]) if pool else None
        row["pred"] = pool[best][0] if pool else []
        row["candidates"] = [{"pron": p, "source": s, "p": round(share[i], 3)} for i, (p, s) in enumerate(pool)]
        row["oracle"] = any(min(distance(p, t) for t in truths(item)) == 0 for p, _ in pool)
        row["seconds"] = elapsed / len(items)
        rows.append(score(row, item))
    return rows, call


METHODS = {
    "lookup": ("code", lambda item: bare_list(item["truth"][0])),
    "espeak": ("code", lambda item: espeak.generate(item["word"])),
    "wikipron": ("code", lambda item: (wiki_variants(item["word"]) or [[]])[0]),
    "checked": ("checked", None),
    "unit": ("code", lambda item: (unitg2p.generate(item["word"], 1) or [[]])[0]),
    "pool-jev": ("pick", dict(use_hints="respell+rhyme")),
    "pool-jev-plain": ("pick", dict(use_hints="respell")),
    "pool-jev-ipa": ("pick", dict(use_hints="ipa")),
    "pool-jev-ipa-rhyme": ("pick", dict(use_hints="ipa+rhyme")),
}


def summarize(rows, cost, started):
    n = max(len(rows), 1)
    summary = {
        "words": len(rows), "exact_rate": round(sum(r["exact"] for r in rows) / n, 4),
        "within_one": round(sum(r["edit"] <= 1 for r in rows) / n, 4),
        "phone_error": round(sum(r["edit"] for r in rows) / max(sum(r["phones"] for r in rows), 1), 4),
        "per_thousand": round(cost / n * 1000, 4), "seconds_per_word": round(sum(r["seconds"] for r in rows) / n, 5),
        "wall_seconds": round(time.time() - started, 1),
    }
    flagged = [r for r in rows if "flag" in r]
    if flagged:
        agreed = [r for r in flagged if r["flag"] == "agree"]
        rest = [r for r in flagged if r["flag"] != "agree"]
        summary["accepted_rate"] = round(len(agreed) / len(flagged), 4)
        summary["accepted_exact"] = round(sum(r["exact"] for r in agreed) / max(len(agreed), 1), 4)
        summary["rest_exact"] = round(sum(r["exact"] for r in rest) / max(len(rest), 1), 4)
    oracles = [r for r in rows if "oracle" in r]
    if oracles:
        summary["oracle_rate"] = round(sum(r["oracle"] for r in oracles) / len(oracles), 4)
    return summary


def run_method(method, set_name, name):
    items = load_set(set_name)
    started = time.time()
    kind, spec = METHODS[method]
    if kind == "code":
        rows, cost = [run_code(it, spec) for it in items], 0.0
    elif kind == "checked":
        rows, cost = [run_checked(it) for it in items], 0.0
    else:
        rows, call = run_pick(items, name, **spec)
        cost = call.cost
    payload = {"experiment": name, "method": method, "set": set_name, "created": time.strftime("%Y-%m-%d %H:%M"), "summary": summarize(rows, cost, started), "words": rows}
    path = root_path(f"results/pron/{name}.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=0))
    return payload["summary"]

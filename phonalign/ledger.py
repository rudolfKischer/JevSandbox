import json
import threading

from .config import SETTINGS, root_path

_LOCK = threading.Lock()


class BudgetExceeded(Exception):
    pass


def ledger_file():
    path = root_path(SETTINGS["ledger_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cost_of(usage):
    inputs = usage.get("input_tokens", 0) * SETTINGS["price_per_million_input_tokens"]
    outputs = usage.get("output_tokens", 0) * SETTINGS["price_per_million_output_tokens"]
    return (inputs + outputs) / 1_000_000


def entries():
    path = ledger_file()
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def spent():
    return sum(cost_of(entry["usage"]) for entry in entries())


def record(label, usage, questions):
    row = {"label": label, "usage": usage, "questions": questions}
    with _LOCK, ledger_file().open("a") as handle:
        handle.write(json.dumps(row) + "\n")


def guard(estimated_tokens):
    projected = spent() + estimated_tokens * SETTINGS["price_per_million_input_tokens"] / 1_000_000
    if projected > SETTINGS["budget_usd"]:
        raise BudgetExceeded(f"projected ${projected:.4f} exceeds budget ${SETTINGS['budget_usd']}")

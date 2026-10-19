import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import ledger
from .config import ROOT, SETTINGS, root_path


class JevError(Exception):
    pass


def load_key():
    value = os.environ.get(SETTINGS["key_env"])
    if not value:
        override = os.environ.get(SETTINGS["key_file_env"])
        path = Path(override) if override else ROOT / SETTINGS["default_key_file"]
        value = path.read_text()
    return value.strip().split("=")[-1].strip().strip("\"'")


def estimate_tokens(payload):
    return int(len(json.dumps(payload)) / SETTINGS["chars_per_token"])


def cache_path(payload):
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    folder = root_path(SETTINGS["cache_dir"])
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{digest}.json"


def post(payload):
    request = urllib.request.Request(
        SETTINGS["endpoint"],
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {load_key()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=SETTINGS["timeout_seconds"]) as reply:
        return json.loads(reply.read())


def post_with_retry(payload):
    retry = SETTINGS["retry"]
    for attempt in range(retry["attempts"]):
        try:
            return post(payload)
        except urllib.error.HTTPError as error:
            body = error.read().decode(errors="replace")[:300]
            if error.code not in retry["statuses"] or attempt == retry["attempts"] - 1:
                raise JevError(f"HTTP {error.code}: {body}") from None
        time.sleep(retry["base_delay"] * 2**attempt)


def evaluate(state, questions, label="adhoc"):
    if len(questions) > SETTINGS["max_questions_per_request"]:
        raise JevError(f"{len(questions)} questions exceeds the per-request cap")
    payload = {"model": SETTINGS["model"], "state": state, "questions": questions}
    path = cache_path(payload)
    if path.exists() and not SETTINGS.get("no_cache"):
        stored = json.loads(path.read_text())
        stored["response"]["_elapsed"] = stored.get("elapsed")
        return stored["response"]
    ledger.guard(estimate_tokens(payload))
    started = time.time()
    response = post_with_retry(payload)
    elapsed = time.time() - started
    ledger.record(label, response.get("usage", {}), len(questions))
    path.write_text(json.dumps({"response": response, "elapsed": elapsed}))
    response["_elapsed"] = elapsed
    return response

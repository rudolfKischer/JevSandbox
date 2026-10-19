import json


def strip(path, data):
    if not path.endswith(".json"):
        return data
    document = json.loads(data)
    rows = document.get("words") if isinstance(document, dict) else None
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            row.pop("nettalk", None)
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()

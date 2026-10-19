import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = json.loads((ROOT / "settings.json").read_text())


def root_path(relative):
    return ROOT / relative


PROMPTS = json.loads((ROOT / "phonalign" / "prompts.json").read_text())

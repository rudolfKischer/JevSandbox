import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.config import SETTINGS


def sound_id(arpabet, names):
    return SETTINGS["notation"]["sound_prefix"] + names[arpabet]


def build(workspace):
    names = json.loads((workspace / SETTINGS["notation"]["og_source"]).read_text())["arpabet_to_og"]
    copy = json.loads((workspace / SETTINGS["notation"]["review_source"]).read_text())["phonemes"]
    rows = {}
    for arpabet in names:
        entry = copy.get(sound_id(arpabet, names), {})
        rows[arpabet] = {
            "ipa": entry.get("l", f"/{arpabet}/").replace("/", "").strip(),
            "plain": entry.get("b", f"/{arpabet}/").replace("/", "").strip(),
            "dictionary": entry.get("h", f"/{arpabet}/").replace("/", "").strip(),
            "example": entry.get("n", ""),
        }
    return rows


def main():
    workspace = (ROOT / SETTINGS["notation"]["workspace"]).resolve()
    rows = build(workspace)
    target = ROOT / SETTINGS["notation"]["target"]
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(rows)} sounds written to {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

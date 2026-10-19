import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phonalign.methods import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"senses", "kinds"}


def flags(config):
    out = []
    if config.get("catalog_in_state"):
        out.append("--catalog")
    if config.get("examples"):
        out.append("--examples")
    if config.get("rules") is False:
        out.append("--no-rules")
    if config.get("scheme") and config["scheme"] != "teaching":
        out += ["--scheme", config["scheme"]]
    if config.get("wording") and config["wording"] != "literal":
        out += ["--wording", config["wording"]]
    if config.get("gate_router") is False:
        out.append("--no-gate")
    if config.get("unit_notes"):
        out.append("--notes")
    return out


def main():
    only = set(sys.argv[1:])
    for path in sorted((ROOT / "results").glob("*.json")):
        data = json.loads(path.read_text())
        if data["method"] in SKIP or (data["method"] != "baseline" and data["method"] not in REGISTRY) or (only and data["experiment"] not in only):
            continue
        command = [sys.executable, "-I", str(ROOT / "scripts" / "run_experiment.py"), data["experiment"], "--method", data["method"], "--notation", data["config"]["notation"], "--gold", data["gold"], *flags(data["config"])]
        if data.get("batch"):
            command += ["--batch", str(data["batch"])]
        if data["method"] != "baseline" and data.get("live") is not False:
            command.append("--live")
        result = subprocess.run(command, capture_output=True, text=True)
        status = "ok" if result.returncode == 0 else "FAILED " + result.stderr[-200:]
        print(data["experiment"], status)


if __name__ == "__main__":
    main()

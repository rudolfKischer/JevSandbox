import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.pron.runner import METHODS, run_method

if __name__ == "__main__":
    name, method, set_name = sys.argv[1:4]
    print(json.dumps(run_method(method, set_name, name)))

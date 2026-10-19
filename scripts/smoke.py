import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign.client import evaluate
from phonalign.gold import load_gold
from phonalign.questions import build_questions, build_state

entry = next(e for e in load_gold() if e["id"] == sys.argv[1])
state, questions = build_state(entry), build_questions(entry)
reply = evaluate(state, questions, label="smoke")
print(json.dumps(state, ensure_ascii=False))
print(json.dumps(questions["p0"], ensure_ascii=False)[:400])
print(json.dumps({"usage": reply.get("usage"), "model": reply.get("model"), "keys": list(reply)}))
print(json.dumps(reply["answers"]["p0"], ensure_ascii=False)[:700])
print(json.dumps(reply["answers"]["s3"], ensure_ascii=False))

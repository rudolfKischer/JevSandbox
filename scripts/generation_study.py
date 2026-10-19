import json
import random
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from phonalign import lexicon
from phonalign.dialect import ipa
from phonalign.models import bare

COUNT = 300
TOKENS = None


def tokenize(text):
    global TOKENS
    if TOKENS is None:
        data = ipa.table()
        keys = set(data["singles"]) | set(data["syllabic"]) | set(data["centring"]) | set(data["diphthong_tokens"])
        TOKENS = sorted(keys, key=len, reverse=True)
    text = "".join(ch for ch in text if ch not in "ˈˌ. \n")
    out, i = [], 0
    while i < len(text):
        for token in TOKENS:
            if text.startswith(token, i):
                out.append(token)
                i += len(token)
                break
        else:
            out.append(text[i])
            i += 1
    return out


def espeak(word, voice):
    done = subprocess.run(["espeak", "-q", "--ipa", "-v", voice, word], capture_output=True, text=True)
    return ipa.convert(tokenize(done.stdout.strip()))


def distance(a, b):
    row = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, row[0] = row[0], i
        for j in range(1, len(b) + 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
    return row[-1]


def llama(word):
    body = {"model": "llama3.2:3b", "stream": False, "options": {"temperature": 0, "num_predict": 40},
            "messages": [{"role": "user", "content": f"Give the CMU Pronouncing Dictionary ARPAbet pronunciation of the English word '{word}'. Answer with the phones only, separated by spaces, with stress digits."}]}
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as reply:
        text = json.loads(reply.read())["message"]["content"]
    return [bare(p) for p in text.upper().replace(",", " ").split() if p.isalpha() or p[:-1].isalpha()]


def evaluate(name, produce, words):
    exact = close = phones = errors = 0
    started = time.time()
    for word in words:
        truth = [tuple(bare(p) for p in v.split()) for v in lexicon.entries()[word]]
        guess = produce(word)
        if guess is None:
            continue
        guess = tuple(guess)
        best = min(distance(guess, t) for t in truth)
        exact += best == 0
        close += best <= 1
        errors += best
        phones += min(len(t) for t in truth)
    n = len(words)
    print(f"{name:<28} exact {exact / n:.0%}  within one phone {close / n:.0%}  phone errors {errors / phones:.0%}  {(time.time() - started) / n * 1000:.0f} ms/word")


def main():
    ranks = lexicon.ranks()
    bands = {"top 10,000": (0, 10000), "10,000 to 40,000": (10000, 40000), "past 40,000": (40000, 10**9)}
    for label, (low, high) in bands.items():
        words = [w for w in lexicon.entries() if w.isalpha() and low < ranks.get(w, 10**9) <= high and len(w) >= 3]
        random.Random(4).shuffle(words)
        words = words[:COUNT]
        evaluate(f"eSpeak US, {label}", lambda w: espeak(w, "en-us"), words)
        if low == 0:
            evaluate("eSpeak UK vs US dictionary", lambda w: espeak(w, "en-gb"), words)
            evaluate("Llama 3.2 3B", llama, words[:60])


if __name__ == "__main__":
    main()

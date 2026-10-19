import subprocess

from ..dialect import ipa

_TOKENS = []
IGNORED = "ˈˌ. \n"


def tokens():
    if not _TOKENS:
        data = ipa.table()
        keys = set(data["singles"]) | set(data["syllabic"]) | set(data["centring"]) | set(data["diphthong_tokens"])
        _TOKENS.extend(sorted(keys, key=len, reverse=True))
    return _TOKENS


def tokenize(text):
    text = "".join(ch for ch in text if ch not in IGNORED)
    out, i = [], 0
    while i < len(text):
        for token in tokens():
            if text.startswith(token, i):
                out.append(token)
                i += len(token)
                break
        else:
            out.append(text[i])
            i += 1
    return out


def generate(word, voice="en-us"):
    done = subprocess.run(["espeak", "-q", "--ipa", "-v", voice, word], capture_output=True, text=True)
    return ipa.convert(tokenize(done.stdout.strip()))

import json

from ..config import root_path

_CACHE = {}
IGNORED = set("ˈˌ.‿|ˑ·")


def table():
    if not _CACHE:
        _CACHE.update(json.loads(root_path("data/ipa_arpabet.json").read_text()))
    return _CACHE


def clean(token):
    return "".join(ch for ch in token if ch not in IGNORED).replace("ʰ", "").replace("ʲ", "").replace("̯", "").replace("̃", "")


def convert(tokens):
    """IPA tokens (a list, one per sound) to a bare ARPAbet-style list. Unknown tokens come back as None."""
    data = table()
    tokens = [clean(t) for t in tokens if clean(t)]
    out, i = [], 0
    while i < len(tokens):
        pair = " ".join(tokens[i:i + 2])
        token = tokens[i]
        if pair in data["pairs"]:
            out.append(data["pairs"][pair])
            i += 2
        elif pair in data["centring"]:
            out.extend(data["centring"][pair])
            i += 2
        elif token in data["diphthong_tokens"]:
            out.append(data["diphthong_tokens"][token])
            i += 1
        elif token in data["centring"]:
            out.extend(data["centring"][token])
            i += 1
        elif token in data["syllabic"]:
            out.extend(data["syllabic"][token])
            i += 1
        elif token in data["singles"]:
            out.append(data["singles"][token])
            i += 1
        else:
            return None
    return out


def load_wikipron(path):
    words = {}
    for line in path.read_text().splitlines():
        word, _, ipa = line.partition("\t")
        if not word.isalpha() or not word.islower():
            continue
        phones = convert(ipa.split())
        if phones:
            words.setdefault(word, set()).add(tuple(phones))
    return words

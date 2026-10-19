import json

from .. import lexicon
from ..config import root_path
from ..models import bare
from ..dialect.rules import VOWELS

_CACHE = {}
RHYME_RANK = 8000


def respelling():
    if "respell" not in _CACHE:
        _CACHE["respell"] = json.loads(root_path("data/respell.json").read_text())
    return _CACHE["respell"]


def respell(phones):
    return "-".join(respelling().get(bare(p), bare(p).lower()) for p in phones)


def tail_of(phones):
    clean = [bare(p) for p in phones]
    for index in range(len(clean) - 1, -1, -1):
        if clean[index] in VOWELS:
            return tuple(clean[index:])
    return tuple(clean)


def tails():
    if "tails" not in _CACHE:
        ranks, index = lexicon.ranks(), {}
        for word, prons in lexicon.entries().items():
            if word.isalpha() and ranks.get(word, 10**9) <= RHYME_RANK and len(word) >= 3:
                for pron in prons:
                    index.setdefault(tail_of(pron.split()), []).append((ranks[word], word))
        _CACHE["tails"] = {tail: sorted(items) for tail, items in index.items()}
    return _CACHE["tails"]


def rhyme_word(phones, word):
    for _, other in tails().get(tail_of(phones), []):
        if other != word and not other.startswith(word[:3]) and not word.startswith(other[:3]):
            return other
    return None


def ipa_text(phones):
    from .. import pronunciation
    return " ".join(pronunciation.ipa_of(p) for p in phones)


def describe(phones, word, style="respell+rhyme"):
    if style is True:
        style = "respell+rhyme"
    if style is False:
        style = "respell"
    text = ipa_text(phones) if style.startswith("ipa") else respell(phones)
    if "rhyme" not in style:
        return text
    rhyme = rhyme_word(phones, word)
    return f"{text} (ends like '{rhyme}')" if rhyme else text

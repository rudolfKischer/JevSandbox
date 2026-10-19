import json

from .config import root_path
from .models import bare

_NOTATION = {}


def notation():
    if not _NOTATION:
        _NOTATION.update(json.loads(root_path("data/notation.json").read_text()))
    return _NOTATION


def phones(text):
    return text.split()


def ipa_of(phone):
    symbol = bare(phone)
    stress = phone[len(symbol):]
    if symbol == "AH":
        return "ʌ" if stress in ("1", "2") else "ə"
    if symbol == "ER":
        return "ɝ" if stress in ("1", "2") else "ɚ"
    return notation()[symbol]["ipa"]


def render(phone_list, mode):
    if mode == "ipa":
        return " ".join(ipa_of(phone) for phone in phone_list)
    if mode == "arpabet":
        return " ".join(bare(phone) for phone in phone_list)
    return f"{render(phone_list, 'arpabet')}  =  {render(phone_list, 'ipa')}"


def respell(phone):
    path = root_path("data/respell.json")
    return json.loads(path.read_text())[bare(phone)]

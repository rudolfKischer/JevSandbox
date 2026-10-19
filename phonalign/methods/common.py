from .. import pronunciation
from ..models import bare


def symbol(phone, mode):
    if mode == "respell":
        return pronunciation.respell(phone)
    return pronunciation.ipa_of(phone) if mode == "ipa" else bare(phone)


def marked_pron(phones, marks, mode):
    if mode == "both":
        return f"{marked_pron(phones, marks, 'arpabet')}  =  {marked_pron(phones, marks, 'ipa')}"
    parts = []
    for index, phone in enumerate(phones):
        text = symbol(phone, mode)
        opens = index in marks and index - 1 not in marks
        closes = index in marks and index + 1 not in marks
        parts.append(("[" if opens else "") + text + ("]" if closes else ""))
    return ("-" if mode == "respell" else " ").join(parts)

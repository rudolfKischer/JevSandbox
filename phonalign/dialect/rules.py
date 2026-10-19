from ..models import bare

VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
ALVEOLAR = {"T", "D", "N", "S", "Z", "TH", "L"}
YOD_SPELLINGS = ("u", "ew", "eu", "ue", "ui")
BATH_TRIGGERS = {"F", "S", "TH"}
CENTRING = {"AA": None, "AO": None, "EH": "AH", "IH": "AH", "UH": "AH", "AY": "AH", "AW": "AH", "OY": "AH"}


def non_rhotic(phones):
    out = []
    for i, phone in enumerate(phones):
        symbol = bare(phone)
        nxt = bare(phones[i + 1]) if i + 1 < len(phones) else ""
        if symbol == "R" and nxt not in VOWELS:
            before = bare(out[-1]) if out else ""
            if before in CENTRING:
                if CENTRING[before]:
                    out.append(CENTRING[before])
                continue
            out.append("AH")
            continue
        if symbol == "ER" and phone.endswith("0"):
            out.extend(["AH0", "R"] if nxt in VOWELS else ["AH0"])
            continue
        out.append(phone)
    return out


def yod(phones, word):
    if not any(s in word for s in YOD_SPELLINGS):
        return phones
    out = []
    for i, phone in enumerate(phones):
        if bare(phone) == "UW" and phone.endswith("1") and out and bare(out[-1]) in ALVEOLAR:
            out.append("Y")
        out.append(phone)
    return out


def bath(phones):
    out = list(phones)
    for i, phone in enumerate(out):
        if bare(phone) != "AE" or not phone.endswith("1"):
            continue
        nxt = bare(out[i + 1]) if i + 1 < len(out) else ""
        after = bare(out[i + 2]) if i + 2 < len(out) else ""
        fricative = nxt in BATH_TRIGGERS and (after not in VOWELS)
        nasal = nxt == "N" and after in {"T", "S", "CH", "D"} and i + 3 <= len(out)
        if fricative or nasal:
            out[i] = "AA1"
    return out


def us_to_uk(phones, word, steps=("rhotic", "yod", "bath")):
    out = list(phones)
    if "bath" in steps:
        out = bath(out)
    if "yod" in steps:
        out = yod(out, word)
    if "rhotic" in steps:
        out = non_rhotic(out)
    return out


WEAK_I_SPELLINGS = {"i", "e", "y", "ie", "ei"}


def weak_vowels(phones, units):
    """In RP an unstressed vowel spelled i, e or y is usually IH, where General American has AH."""
    out, index = list(phones), 0
    for unit in units:
        for k, _ in enumerate(unit.sounds):
            phone = out[index]
            if bare(phone) == "AH" and phone.endswith("0") and unit.spelling in WEAK_I_SPELLINGS:
                out[index] = "IH0"
            index += 1
    return out


CANADIAN_OVERRIDES = {
    "lieutenant": "L EH0 F T EH1 N AH0 N T",
    "process": "P R OW1 S EH2 S",
    "processes": "P R OW1 S EH2 S AH0 Z",
    "project": "P R OW1 JH EH0 K T",
    "progress": "P R OW1 G R EH2 S",
    "pasta": "P AE1 S T AH0",
    "drama": "D R AE1 M AH0",
    "taco": "T AE1 K OW0",
    "sorry": "S AO1 R IY0",
    "borrow": "B AO1 R OW0",
    "tomorrow": "T AH0 M AO1 R OW0",
}


def canadian(phones, word):
    """General American with the cot-caught merger and a short list of Canadian words. Unverified against data."""
    if word in CANADIAN_OVERRIDES:
        return CANADIAN_OVERRIDES[word].split(), True
    out, changed = [], False
    for i, phone in enumerate(phones):
        nxt = bare(phones[i + 1]) if i + 1 < len(phones) else ""
        if bare(phone) == "AO" and nxt != "R":
            out.append("AA" + phone[2:])
            changed = True
        else:
            out.append(phone)
    return out, changed

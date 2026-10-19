# Towards one unified word dataset

The word explorer shows these fields for each word (from `/api/word/<word>`): alignment, phonogram_analysis, phonemes, pronunciations,
syllables, concepts, morphemes, origins, definitions with part of speech, heteronym, irregularity_reasons, frequency, sight-word status.
The aim is to generate every field in one pipeline, per pronunciation, per dialect and per meaning. This is where each field stands in the lab.

| field | source today | in the lab | status |
| --- | --- | --- | --- |
| spelling, frequency, rank | word list and frequency table | lookup | nothing to generate |
| US pronunciation | CMU | Pronunciation page | lookup covers 63,200 of 67,400 words. For the rest: eSpeak generates (74% exact on common words, 50% on rare). A second dictionary agreeing makes 43% of random words auto-accepted at 92% exact, and the rest go to a person |
| UK pronunciation | none | Regions page | rules from US reach 84% (match to a WikiPron UK variant). eSpeak's UK voice reaches 93%. Pick eSpeak UK, check against WikiPron, flag the rest |
| Canadian pronunciation | none | Regions page | rules from the literature only (merger plus a short word list). No data to check them |
| pronunciation by meaning (heteronyms) | Wiktionary and a curated list | Pronunciation page, Heteronyms set | Jev picks the pronunciation for a meaning at 56 to 69%. Not good enough. Next: have Jev label the sense, then look the pronunciation up |
| phonemes | derived from the pronunciation | n/a | deterministic |
| alignment (spelling units to sounds, silent letters) | statistical aligner | Alignment page | catalog candidates plus one Jev question: 97.7% on the curated set, 95.9% judged correct on 1,000 hard words, $0.023 per 1,000 words |
| irregularity reasons | rules | Alignment page | the candidate search already knows when a word needs a unit outside the catalog (cost above zero). That is a ready-made irregularity flag |
| letter words, initialisms, abbreviations | origins data | Alignment page, router | 42 of 42 initialisms and 35 of 35 abbreviations right. Plural initialisms now handled. Mixed words (JPEG) are flagged |
| origins (loan, name, acronym) | Wikipedia lists, names, Wiktionary | router kind question | 31 of 31 on the kinds test. Not yet run over the whole list |
| concepts (r-controlled, blends, silent e, digraphs, vowel teams, double consonants) | rules over the alignment | Alignment page chips | detectors written. r-controlled matches our teaching units on 139 of 139 words |
| concepts that need syllables or morphology (open and closed syllables, welded sounds, suffix rules) | rules | not yet | next: add syllable boundaries to the alignment and derive these |
| syllables | CMU syllabified file | not yet | could be Jev picking among candidate splits, as with the alignment |
| morphemes (prefix, root, suffix) | morphology data | not yet | same pattern: code lists candidate splits from an affix list, Jev picks. Would also help alignment (th across hot|house) |
| definitions, part of speech, examples | Wiktionary and WordNet | not yet | lookup. The only generated part is pairing a definition with a pronunciation |

## Pattern that keeps working
Code produces a short list of valid candidates from a knowledge source (the unit catalog, a dictionary, an affix list).
Jev chooses among them when the choice is a judgement about meaning or convention (is qu one unit, which sense of read).
Jev is not used to judge how something sounds. It prefers whatever looks like the spelling, so sound judgements come from
dictionaries and rules, not from Jev.

## Proposed record
One record per word, with a list of readings. Each reading carries its own dialect, meaning, sounds, alignment and flags,
plus where it came from and whether a person has confirmed it.

```json
{
  "word": "read",
  "frequency_rank": 175,
  "readings": [
    {"dialect": "us", "sense": "to look at written words", "pos": "verb",
     "phones": ["R", "IY1", "D"], "units": [["r", ["R"]], ["ea", ["IY1"]], ["d", ["D"]]],
     "concepts": ["vowel team"], "kind": "word",
     "source": {"phones": "cmu", "units": "catalog pick"}, "review": "unreviewed"},
    {"dialect": "uk", "sense": "to look at written words", "phones": ["R", "IY1", "D"], "units": "same", "source": {"phones": "rules from us"}},
    {"dialect": "us", "sense": "past tense of read", "phones": ["R", "EH1", "D"], "units": [["r", ["R"]], ["ea", ["EH1"]], ["d", ["D"]]]}
  ],
  "morphemes": [["read", "root"]],
  "origins": [],
  "flags": {"unsure_below": 0.7, "needs_review": false}
}
```

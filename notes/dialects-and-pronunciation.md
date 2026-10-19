# Pronunciations and dialects

Questions: can we generate pronunciations, and can we handle the standard differences between US, UK and Canadian English?
Jev cannot generate text, so "generate" here means code or another tool produces candidates, and Jev or a person chooses.

## What differs between standard varieties
From the [GA and RP comparison](https://en.wikipedia.org/wiki/Comparison_of_General_American_and_Received_Pronunciation) and the
[Canadian raising](https://en.wikipedia.org/wiki/Canadian_raising) pages:
- Rhoticity: US says the r after a vowel (car /kɑr/), UK does not (car /kɑː/). Biggest by far.
- Weak vowels: unstressed vowels spelled i, e, y are /ɪ/ in UK and /ə/ in US (business, women, started).
- BATH vowel: bath, dance, answer have /æ/ in US and /ɑː/ in UK.
- Yod: tune, new, duty keep /j/ in UK and lose it in US.
- LOT vowel: unrounded in US, rounded in UK. Both fall in one symbol in CMU-style notation, so it does not show up.
- Flapping: US /t/ in butter becomes a flap. UK may use a glottal stop. Not visible in CMU either.
- A handful of words (schedule, tomato, garage, lieutenant).
- Canadian: mostly General American. Raising of the vowel in out and about before a voiceless consonant, cot and caught merged,
  pasta and drama with a front vowel, zed, lieutenant as lef-ten-ant, and vowels before r kept apart (sorry, borrow).
  None of these change which letters spell which sounds, so Canadian can share the US alignment.

## How often it matters
WikiPron's US and UK lists ([WikiPron](https://pypi.org/project/wikipron/)), 6,104 words in the top 8,000, mapped to our symbols:
- 80% have the same pronunciation in both.
- 10% differ only in rhoticity.
- 1% BATH vowel, under 1% yod, about 8% other (weak vowels, stress, one-off words).

## Generating a UK pronunciation from the US one (code only)
Rules: drop r unless a vowel follows, keep a linking r, final ER becomes schwa, yod after alveolars before u spellings, BATH vowel,
and unstressed vowels spelled i, e, y become IH. The last one uses the alignment, which is how alignment helps generation.
Match with at least one WikiPron UK variant, on 6,080 words:
- copy the US pronunciation: 66%
- rhoticity rules: 80%
- plus weak vowels by spelling: 84%

The rest are word-by-word cases and variant spellings of the same word. A short exceptions list would be the next step.

## Does alignment survive a dialect change?
With a small addition to the unit table (vowel plus r units may drop the r), I aligned the rule-generated UK pronunciations of the
186 curated words. The spelling units were identical to the US alignment for 178 words (teaching scheme) and 175 (grapheme scheme).
The differences were ones like laugh (BATH vowel in a unit the catalog lists as short a) and er endings.
So one alignment procedure serves all the standard varieties. No dialect-specific catalog is needed.

## Generating a pronunciation from spelling alone (words we do not have)
Compared with CMU on random words, exact match and within one phone:
| tool | top 10,000 | 10,000 to 40,000 | past 40,000 |
| --- | --- | --- | --- |
| eSpeak, US voice (installed, 7 ms/word) | 74%, 88% | 59%, 85% | 50%, 74% |
| eSpeak, UK voice against the US dictionary | 63%, 88% | | |
| Llama 3.2 3B asked for ARPAbet | 0% | | |
Published neural models reach about a 20% word error rate on CMU, so about 80% right
([Transformer G2P](https://arxiv.org/pdf/2004.06338)). That is the ceiling for free tools. A small local LLM cannot do it.
Jev cannot produce text, and it was a coin flip at choosing a pronunciation from a meaning, so it is not the tool for this.

## Recommendation
1. Store one US pronunciation per word from CMU (63,200 of your 67,400 words). Treat Canadian as US.
2. Generate UK from US by the rules above, for the 84% of words that match, and flag the rest. Add an exceptions list for the common ones.
3. For the 4,200 words with no CMU entry, use eSpeak for a first guess. Accept it where it agrees with a second source
   (WikiPron, another voice). Everything else goes to a person.
4. Align each dialect's pronunciation with the same method. Check that the unit spans agree across dialects, and flag the words where they do not.

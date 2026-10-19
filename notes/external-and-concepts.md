# External sources, and how alignment relates to teaching concepts

## Sources found
| source | what it is | used? |
| --- | --- | --- |
| [NETtalk corpus](https://archive.ics.uci.edu/dataset/150/connectionist+bench+nettalk+corpus) (Sejnowski and Rosenberg 1988) | 20,008 words, each letter aligned to a phoneme or a dash, hand annotated | Yes. 136 of our gold words are in it |
| [Dictionary of the British English Spelling System](https://www.openbookpublishers.com/books/10.11647/obp.0053) (Brooks 2015) | Open access reference: 284 graphemes, 543 correspondences, 89 graphemes in the main system | Not downloadable: the publisher gates it behind a CAPTCHA, which I left alone. A person could download the PDF by hand |
| Gontijo, Gontijo and Shillcock 2003 | Grapheme-phoneme probabilities for British English: 195 graphemes, 461 correspondences ([abstract](https://researchportal.hw.ac.uk/en/publications/grapheme-phoneme-probabilities-in-british-english/)) | Paper only |
| [m2m-aligner](https://packages.debian.org/experimental/m2m-aligner), [Phonetisaurus](https://montreal-forced-aligner.readthedocs.io/en/latest/reference/g2p_modeling/generated/montreal_forced_aligner.g2p.phonetisaurus_trainer.PhonetisaurusTrainerMixin.html) | EM many-to-many aligners that learn alignments from a pronouncing dictionary, no labels | Not installed. Our existing aligner is the same family |
| [WikiPron](https://pypi.org/project/wikipron/) | Pronunciations mined from Wiktionary, by dialect. No alignment | Not used. Useful later for dialect pronunciations |
| ByT5 and Conformer G2P models ([NeMo](https://docs.nvidia.com/nemo/speech/nightly/tts/g2p.html)) | Predict phonemes from spelling. No alignment | No |
| Forced aligners (Montreal) | Align phones to audio, not to letters | No. We have no audio |
| [Grapheme classification paper](https://arxiv.org/html/2404.01953v1) | 10,000 words hand segmented by England's National Curriculum rules. Not released | No |

Licence note: the UCI page says CC BY 4.0, while the file header says non-commercial research use. The data is kept in
`data/external/`, which is git-ignored, and is used only for this comparison.

## What NETtalk shows
NETtalk puts each phoneme on one letter and marks other letters with a dash. It does not group letters. It does show
which letters carry a sound. Silent letters and the second letter of a digraph are both dashes.

We compared our gold unit by unit: does each of our units hold exactly one sounding letter in NETtalk, and each silent
unit none? Silent letters stay out of it, since which side they attach to is a convention.

- 113 of 136 words (83%) match.
- Nearly every disagreement is one thing. NETtalk does not merge vowel plus r (ar, or, air, ear, our, ore, ire: 17 to 38%
  agree) or qu. It gives each letter its own sound. Where r-colouring is a single phoneme (er, ir, ur as ER) it agrees.
- Everything else agrees: consonant digraphs 96%, vowel digraphs 100%, silent pairs (kn, wr, mb, bt, lm) 100%, vowel
  trigraphs and quadgraphs (igh, ough, eigh) 100%, double consonants, x as ks, zz as ts, le with a schwa.

So the gold is about right. The one systematic difference is a choice, not an error.

## Alignment and teaching concepts are different layers
Blends, bossy-r, welded sounds, suffixes and syllable types are things taught about words. Most are not units of
spelling. A unit of spelling is a letter or letter group that spells a sound.

Catalog categories, with NETtalk agreement for those that can be measured:

| category | entries | NETtalk agrees | layer |
| --- | --- | --- | --- |
| single and double consonants, digraphs, trigraphs | 83 + 26 + 5 | 95 to 96% | alignment |
| silent pairs (kn, wr, mb, bt) | 20 | 100% | alignment |
| vowel digraphs, trigraphs, quadgraphs, diphthongs | 42 + 7 + 10 + 10 | 100% | alignment |
| short, long and schwa vowels | 35 + 10 + 6 | 100% | alignment |
| vowel plus r (ar, or, air, ear, ire) | 41 | 38% | concept |
| welded (ang, ink, all) | 20 | not in the gold | concept |
| suffixes (tion, able, ment) and consonant-le | 32 + 10 | 100% | concept, mostly morphology |
| split digraph (a_e), context patterns (qua, wa) | 9 + 3 | n/a | concept |

I added a scheme setting. In the grapheme scheme, vowel plus r and qu are not units, so car is c, a, r. Concepts are then found
afterwards from the alignment (`phonalign/concepts.py`): r-controlled, blends, silent e, consonant digraph, vowel team,
double consonant, silent letter.

- Accuracy does not change. Catalog pick with the catalog in context: 95.7% teaching scheme, 95.0% grapheme scheme.
- Agreement with NETtalk rises from 82% to 94%.
- The r-controlled flag found from the grapheme alignment matches the flag from our teaching units on 139 of 139 words.

Recommendation: align at the grapheme level, then derive r-controlled, blends and silent e from the result, and take
morphology (prefixes, suffixes) from a separate source. That keeps one alignment that works for all concepts, and changing
what counts as a concept never means re-aligning. This is your call: if a tutor wants `ar` treated as one phonogram
unit, the teaching scheme still works at the same accuracy.

## Local models
A small local model can only choose among the catalog candidates, the same question as the catalog pick.
Llama 3.2 3B gets 73% and the 1B gets 48%, below the 88% of simply taking the longest units. The first 1B number
(93%) was an artefact: the candidate labelled `a` was always the best by the length rule, and a model that leans toward `a`
scores well. Labels and order are now shuffled per word. Jev gets the same fix, and its score without the catalog fell from
93% to 89%, while with the catalog it holds at 95 to 96%.

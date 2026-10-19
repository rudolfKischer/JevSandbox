# Where this work can help the word explorer

Written 2026-10-19 from the explorer notes (`notes/issue-10-phonograms/`, `observations/`) and measurements on the local data. Read only: nothing in the three repos was changed.

## What the explorer's aligner is
`data/g2p_aligned.json` is the public Phonetisaurus alignment of CMUdict. The explorer's own Viterbi aligner (`scripts/aligner`, `data/alignment-model.json`) is trained on those alignments (about 735k occurrences, 502 units) and groups silent letters by rules. Its output is `word_graphemes` in `words.db`.

## Measurements

| # | Explorer problem (source) | What we measured | Source of the number |
|---|---|---|---|
| 1 | Alignment correctness is unmeasured: "a dictionary phone match alone must not pass a spelling alignment" (FINDINGS-AND-FIXES, benchmark section) | On 892 random words I had judged right, the explorer's alignment has the same letter groups for 92 to 95% (90% on the hard set). Of 51 differences I read, about 19 were real grouping errors (le + y in ashley, bailey, wortley; se + ar in research; cu as y+oo in accumulated; AH on d or t before le in saddled), the rest conventions (ed, -ism). That is roughly 2% real errors. | `scripts/` comparison, `results/sources` |
| 2 | FIX-05: consonant-le alignments give the schwa to the wrong letter | 350 words have a consonant letter alone spelling AH (battle: t as schwa). About 600 words group a silent e into a consonant unit before a vowel unit (mostly -ley names). Our units give le as schwa + l and keep ey whole. | `words.db word_graphemes` |
| 3 | FIX-08: variant conflicts; the explorer must switch to another dictionary variant or fit with at most two edits | The stored alignment does not match the dictionary's first pronunciation for 6,028 words (9.6% of the bank, 20% of the top 1,000, 18% of the top 10,000). We align the pronunciation we are given. On a random 150 of those words: 149 right, 1 doubtful (99.3%). | `data/samples/uncovered.json`, `results/r-uncovered.json` |
| 4 | Multi-pronunciation eligibility needs a breakdown per pronunciation (`multi-pronunciation-eligibility.md`) | Of 7,256 alternate dictionary pronunciations, 6,773 (93%) align cleanly or with one off-catalog unit, 458 need two, 25 cannot be aligned. Cost also separates real alternates from errors. | `phonalign/pool.best_cost` |
| 5 | Corrections dataset has 17 entries and more wrong dictionary pronunciations are unseen (word-policy README, item 10) | Alignment cost flags every one of the 8 known bad entries present in our dictionary file (the good variant costs 0, the bad one 1 to 4). 395 variants cost 2 or more above a sibling. Many are legitimate weak, regional or letter-name forms (wh as h+w, am as ay-em), which is what the FIX-08c letter-name guard is for. A frequency-ordered review list is a day of reading. | suspect-variant scan |
| 6 | FIX-06: initialisms and abbreviations, 49 words with no alignment, `me`, `am`, `oh` counted as acronyms | The 20 words that cannot be aligned letter by letter are all abbreviations or initialisms (mr, jr, vs, etc, feb, bbq, kwh). Our router agrees with the explorer's exclusion list on 89 of 103 shared words and flags 28 more, about 16 of which are real abbreviations the list misses (dr, ms, nov, oct, gen, ct, ave) and about 8 are spelling variants it gets wrong (donuts, thru, boro). | `runs/bank-progress.json` |
| 7 | Explorer pattern tags count letters (AGENTS.md: "CV structures currently count letters") | ship is CCVC, thing CCVCC, knight CCVCCC, school CCCVVC. The sound-unit pattern differs from the letter pattern for 77% of the top 1,000 words and 80 to 83% of the rest. | unit patterns from our alignment |
| 8 | Irregularity reasons and `unusual_spelling` | A word's rarest unit probability separates the 233 listed irregular words from the rest of the top 8,000 with AUC 0.77 to 0.79. At a 1e-4 cutoff it flags 35% of the list at a 2.6% false rate and surfaces unlisted candidates (especially, someone, caught, genuine, eighth, bought). | EM unit table |
| 9 | 102,390 frequent words are missing from CMU (`missing_words.tsv`) | Of the 1,429 with zipf 3 or more, most are abbreviations, contractions without an apostrophe (dont, thats), initialisms and brands. WikiPron covers 17%; eSpeak agrees with it on 11% of the sample, which is the part we could add without review. | generate-then-check |
| 10 | Grouping gaps listed as not done: glide patterns (tu, su, du), syllabic m, n, l, French oi, aw | Already handled with stated rulings and units: u as AH+W, s:Z + m:AH+M, oi as W+AA, aw as one unit. | `notes/FINDINGS.md` |

## A gap on our side
Our word bank comes from the older syllabified CMU file. It lacks 3,979 alphabetic words the explorer has: 26 single letters and modern words (facebook, google, obama, twitter, youtube, blog, favourite). Using the same CMU 0.7b package would close it.

## Caveats
- The judged answers are mine, not Kathleen's or yours. The rulings (glides, syllabic consonants, Mc) should be reviewed before anything depends on them.
- "Differs" counts conventions as differences. The 2% real-error figure comes from reading all 51 differences on the random samples (19 real, the rest conventions).
- Which phonograms exist (FIX-02) is a curriculum decision. Our unit frequencies are evidence for it, not an answer.
- Our unit grouping is the grapheme scheme (ar as a + r). The explorer teaches ar as one unit. The aligner supports both schemes.

## Suggested order
1. Use the judged sets as the frozen benchmark the master plan asks for (P2-03 and P2-06), after you review the rulings.
2. Review the suspect-variant list and the router's 28 extra flags, then extend the corrections and origins data.
3. Compute CV patterns from sound units.
4. Try our aligner as the source of per-pronunciation breakdowns behind the multi-pronunciation cache, compared against the Viterbi output on the benchmark first.

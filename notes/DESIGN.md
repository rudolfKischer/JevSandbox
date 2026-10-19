# Design notes

## The constraint
Jev cannot generate text. It answers questions about a state: Choice (one of N), Score (rubric) and
Noul (probability a statement is true). Alignment therefore has to be turned into questions, with our
code owning the search. This matches the docs: atomic questions, parallel, composed in code, gated on
confidence. Known weak spots to design around: counting, position and numbers, first option bias,
literal reading of negations.

## Method 1: per sound choice plus silent letters (implemented)
For each sound in a given pronunciation, one Choice: which letters spell it? Options are every letter span
up to 4 letters, written as the word with brackets (`k[n]ight`, `[kn]ight`), so Jev never has to count.
For each letter, one Noul: is it silent? A small dynamic program then picks the best tiling:

- phone k picks a span; spans move left to right and may not overlap
- two sounds may share one span (x = k+s, qu = k+w, le = uh+l)
- letters skipped between spans are silent and pay the Noul silent score
- a forward pass over all tilings gives the probability of the best one (our confidence)

Cost per word is about 8 to 14 questions. Everything is cached, so a re-run is free.

## Napkin math (estimates, chars/3.5 per token, $0.04 per million input, output free)
| scale | questions | tokens | cost |
| --- | --- | --- | --- |
| gold set, 46 words | 369 | 27k | $0.001 |
| per word | 8 | 580 | $0.00002 |
| 2,000 words | 16k | 1.2M | $0.05 |
| 125,000 words (full CMU) | 1M | 73M | $2.90 |

Multiply by about 3 for senses and dialects. Money is not the limit; latency and rate limits are
(125k requests at about 0.15 s with 6 workers is roughly 1 hour). The real token counts come back in
`usage` and replace these estimates after the first live run.

## What is hard (to try in order)
1. Notation: ARPAbet, IPA or both. Does Jev read them equally well?
2. Silent letters: weight of the silent score against the span score.
3. Conventions: gold says `kn`, `igh`, `ough` are single units. Jev may split them. Decide the
   convention first, then measure; `accept` lists in gold hold legitimate alternatives.
4. Option order bias: try shuffled option order, compare.
5. Pronunciation per sense: Choice among known pronunciations given the definition (heteronyms).
6. Word kind routing before alignment: Choice among ordinary, abbreviation, initialism, letter names,
   loan, name. Letter names and abbreviations take a different path (whole word unit, or letter names).
7. Dialect: same method, pronunciation supplied per dialect; ask Jev only to align, not to invent sounds.
8. Confidence: does the forward probability predict correctness? Calibrate on a few thousand words,
   weak labels from the existing aligner where both agree, then send only low confidence words to a human.

## Gold set
`data/gold/starter.json`: 46 words. Simple, digraph, silent e, silent letters, r controlled, two sounds,
irregular, loan, letter names, abbreviation, heteronym (with senses), dialect. Units are written
`spelling:PHONE+PHONE`, a dash is silent. Stress digits are kept in gold but ignored when scoring.
The current aligner scores 29/41 exact on it, mostly on convention differences (queen, little, car).

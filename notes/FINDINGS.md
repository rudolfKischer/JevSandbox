# Findings, round 6

Three pages in the lab: Alignment, Pronunciation, Regions. Start the viewer with `make serve`. Other notes:
`notes/unified-dataset.md` (every explorer field and where it stands), `notes/dialects-and-pronunciation.md`, `notes/gold-decisions.md`.

## Alignment: the diagnostic set (1,000 hard words)
Chosen to expose failures, not to be a fair sample: 330 words needing a unit outside the catalog, 250 with several valid
breakdowns, 160 flagged unusual, 90 loans, 90 names, 60 long words, 20 flagged initials. I read every answer and marked it right,
doubtful or wrong, with the pattern of the mistake.

| | words | share |
| --- | --- | --- |
| right | 959 | 95.9% |
| doubtful | 30 | 3.0% |
| wrong | 11 | 1.1% |

By group: off-catalog 91%, long words 93%, initials 85%, everything else 98% or better. Names scored 100%, partly because I accepted
any alignment whose every unit is plausible. Read it as a floor on strictness, not a ceiling.

Failure patterns, 41 words: syllabic consonants 8, the tu glide (statute, ritual, factually) 8, odd spellings 5, glide pairs 4,
names 4, and one each of ten smaller patterns.

First pass found 16 wrong and 28 doubtful. Fixes made from those patterns:
- Attested single-letter units had stress digits and never matched. Now l as schwa+L works, which fixed warbling, grumbling,
  troubling, dribbling, recycling, embezzling.
- ks is split like qu (books, yolks).
- A silent e before ly, ment, ness, less and similar suffixes costs nothing (affectionately, indiscriminately).
- Plural initialisms (cds, stds) are handled.
Net: 14 fixed, and 12 new problems from the changed candidate lists (mostly more tu-glide cases). 95.6% to 95.9%.

## Cost: the router and the "70%"
The router asked Jev "what kind of word" for every word. It is now asked only when code sees a reason. Cost on the diagnostic set is
$0.023 per 1,000 words, 15 ms per word. The earlier 70% was the share of confident answers, not accuracy.
This set is judged, so the page now shows a correct percentage. Confidence is no longer a headline.

## Round 7: failure patterns, learned frequencies, clean held-out samples
The 41 failures on the 1,000-word diagnostic set fell into two kinds. In the first, the right candidate was offered but Jev was unsure between
close ones (tu-glide, ei/ie splits). In the second, the right candidate was never offered (catholicism needed m:AH+M, Laughlin needed gh:K).
Both traced to the same root: the unit table held junk (s:Z+AH, m:M+AH, c:S+IY) and off-catalog guesses cost the same whatever they spelled,
so a letter could "spell" a sound it never spells and the statistics then learned it.

What changed, in order of effect:
1. **Learned unit frequencies (EM).** Each word splits one vote among its candidates in proportion to the product of unit probabilities, repeated
   six times over the whole bank (`phonalign/em.py`, `data/em_units.json`). Free, and alone it is right on at least 93 to 98% depending on the set.
2. **Clean the table, price the guesses.** A single consonant letter can no longer spell a vowel sound from the attested list, and an off-catalog
   guess across that line costs 2 more (`cross_penalty`). The EM score subtracts 3 per unit of catalog cost (`em_cost_weight`).
3. **Keep teams whole** (`pool.py`): ei and ie are not cut to hand a letter to a soft c or g (deceived), ll and ss are not split (wallets),
   gu stays together (plaguing), and a syllabic L, M or N never takes a stressed vowel (multipart).
4. **Syllabic m, n, l** after a consonant (tourism = s:Z m:AH0+M), a short curated list of rare units (`data/extra_units.json`: gh as k, Mc as Mac, oi as wa,
   eu as yoo-uh, au as aa, x by its letter name), hard-g as a letter name for MGM.
5. **Skip Jev when EM is sure.** If one candidate has 97% or more of the learned vote, no question is asked; otherwise Jev's answer is blended with EM
   (weight 0.25). Roughly half of ordinary words never reach Jev, so ordinary words cost about $0.0045 per 1,000 and hard ones about $0.010.

Scores (grapheme scheme, catalog in state, batches of 100; "right" is my reading):

| set | right | not right | cost per 1,000 |
| --- | --- | --- | --- |
| curated 264 (gold) | 98.9% | 3 | $0.0097 |
| hard 18 | 94.4% | 1 | $0.012 |
| diagnostic 1,000 | 100% after fixes (95.6% at first reading) | 0 | $0.010 |
| clean held-out, 300 random bank words | 99.0% at first reading (3 doubtful, 0 wrong) | 3, then fixed | $0.0045 |
| second clean held-out, 300 random | 99.0% at first reading (1 wrong, 2 doubtful) | 3, one fixed by a minimum kind confidence of 0.6 | $0.0044 |
| earlier held-out, 300 random | 99.3% | 2 doubtful | $0.0053 |

Read these honestly. The diagnostic set is tuned on, and where two answers were equally defensible I ruled and wrote the ruling next to the word
(glide-pair: the affricate is the consonant's and AH0+W is the u's; syllabic: the schwa goes on the m/n/l; Mc is one unit). The clean held-out sample
is the number to quote: 99.0% before any fix, with doubtful words, not wrong ones. A verdict now belongs to the specific answer I read: another method's
different answer counts as not right until it is read, so the free methods are lower bounds (EM alone at least 93 to 95%, longest units at least 82 to 91%).

Whole bank (62,935 words, one run, $0.39, 3.5 minutes, before the fixes above): 92.5% agree with NETtalk's structure (97% on the top 1,000 words, 91% on rare ones),
71% match the older aligner exactly (different conventions), 94% match the frequency-only pick (which was trained on these words, so not independent),
21,000 words flagged by at least one check. Rerun after the fixes to refresh it.

Remaining weakness: ambiguous placements (silent letters in sovereigns), names, and any word whose pronunciation in the dictionary is wrong (CMU drops the L
in complexions).

## Round 8: independence from other people's alignments, and a source comparison
**Audit.** The only path by which an existing alignment entered the pipeline was `units.add_attested`, which added any unit seen 30 or more times in
`g2p_aligned.json`. That file is the public Phonetisaurus alignment of the CMU dictionary (aligned-cmudict), not a hand-made gold, and it was used for
unit *vocabulary*, never to choose a word's answer. Everything else read from it was comparison only (`baseline_same`, the Phonetisaurus method D/E/O experiments).
The viewer had mislabelled it "our current aligner"; it is Phonetisaurus. The explorer's own aligner (words.db) learned from it, so those two are one family.

**Ablation (free method, 1,890 answers I judged right, plus 13,706 NETtalk words):**

| unit vocabulary | match with my judged answers | NETtalk structure agreement |
| --- | --- | --- |
| catalog + Phonetisaurus counts (before) | 93.7% | 92.05% |
| catalog only | 91.1% | 91.92% |
| catalog + units found by an unsupervised dictionary-only pass | 78.5% (noisy units) | 91.88% |
| catalog + 16 hand-reviewed units (now) | 93.7% | 92.05% |

Only 21 units came from the Phonetisaurus counts (au as AW, u as Y+AH, al as AA, ao, kk, cz ...). I reviewed them and kept the real spelling patterns in
`data/extra_units.json`; the pipeline no longer reads the file (`attested_source` is `none`). The unsupervised pass (`phonalign/m2m.py`, a many-to-many EM aligner
in the style of m2m-aligner) found 107 more candidate units, but most are alignment artefacts (te as T, tio as SH), so it is kept as a comparison source, not a unit list.

**Sources compared** (`make sources`, Sources page): our system (or our frequency pick until a whole-bank run exists), the explorer's aligner, Phonetisaurus,
the unsupervised aligner, and NETtalk. Two answers count as the same structure when they group the sounding letters alike and differ only in where silent letters sit.
A schwa followed by L, M or N is treated as one chunk (a:AH + l:L equals al:AH+L). NETtalk is compared with its own criterion (each unit holds exactly one sounding letter).
The explorer's aligner and Phonetisaurus agree on structure for 99.7% of words, because one was built from the other.

## Pronunciation: can we generate them?
60 hand-picked hard words, 1,000 random words, and 32 heteronym meanings. Truth is the dictionary entry.

| method | starter 60 | random 1,000 | cost per 1,000 | time per word |
| --- | --- | --- | --- | --- |
| eSpeak (rules, free) | 78% | 67.5% | free | 7 ms |
| second dictionary (WikiPron) | 57% | 42% | free | 1 ms |
| unit statistics from our aligned words | 2% | 9% | free | 14 ms |
| eSpeak, accepted only when WikiPron agrees | 89% of the 75% accepted | 92% of the 43% accepted | free | 8 ms |
| candidates plus Jev, IPA | 18% | 25% | $0.011 | 7 ms |
| candidates plus Jev, respelling | 8% to 22% | 20% to 21% | $0.010 | 7 ms |
| candidates plus local Llama 3B | 8% | n/a | free | 930 ms |

The candidate list contains the right answer for 78% and 71% of words, so Jev's picking is the loss. Jev prefers the respelling that looks most like
the spelling (nickname as "nick-nahm"). It cannot judge how something sounds. For heteronym meanings it reaches 59 to 69% with IPA
and a rhyme word, against 56% before and 47% for Llama. The way to trust a generated pronunciation is agreement between two
independent sources, not Jev.

## Regions
- 80% of common words are identical in US and UK, 10% differ only in the r, 8% in weak vowels, stress or one-off words, 1% BATH vowel, under 1% yod.
- Matching a WikiPron UK pronunciation: copy US 66%, drop r 80%, plus yod and BATH 80%, plus weak vowels chosen via the alignment 84%,
  eSpeak UK voice 93%. The same test for the US voice is 89%.
- The alignment works unchanged. 178 of 186 curated words keep identical spelling units under a UK pronunciation.
- Canada: no data. Rules from the literature are shown and marked unverified.

## Next
1. Rerun the whole word bank with the fixes (`make bank-align`, about $0.4, 4 minutes) and read the flagged words for new patterns.
2. Judge another clean random sample after each batch of rule changes; do not tune on it.
3. For pronunciations, build the generate-then-check pipeline with eSpeak (US and UK) and WikiPron as two sources, with a review queue.
4. Sense labelling for heteronyms (Jev labels the sense, a table gives the pronunciation).

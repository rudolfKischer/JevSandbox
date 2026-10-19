# Jev sandbox

Builds a phoneme-aligned phonogram dataset (spelling units paired with sounds) using TypeSafe's Jev, a System One model that returns typed Choice, Score and Noul answers and never text. Code lists every valid split of a word into catalog units, learned frequencies resolve most words, and Jev is asked only about the unsure ones.

## Start

```
make data       download the data bundles (results, bank sets, NETtalk, WikiPron) listed in data/manifest.json
make serve      results viewer at http://127.0.0.1:5010/web/ (fetches missing data first)
make test       unit tests, no network
```

Needs the sibling `OGTutorAssistant` checkout (catalog, CMU dictionary, word bank). The Jev key is read from `TYPESAFE_API_KEY`, else the file named by `JEV_KEY_FILE`, else `../jev_api_key.txt`; it is never stored here. Calls are cached under `.cache/`, logged to `runs/ledger.jsonl`, and refused past `budget_usd` in `settings.json`.

## Large data

Large and generated files are not in git. `data/manifest.json` pins each bundle by version and SHA-256; `scripts/data_bucket.py` downloads it from a GitHub release (`<bundle>-v<N>`), verifies it, and extracts it. Upstream datasets (NETtalk, WikiPron) are downloaded from their own sources and never re-hosted. NETtalk-derived alignments are stripped from published results.

```
python3 scripts/data_bucket.py status                 what is present
python3 scripts/data_bucket.py fetch [bundle ...]     download what is missing
python3 scripts/data_bucket.py publish results --bump pack, upload as the next version, update the manifest
```

After a big run or a regeneration, publish the affected bundle with `--bump` and commit the manifest; old versions stay available under their tags.

## Layout

- `phonalign/` library: `tilings`, `pool`, `units` (candidates), `em` (learned frequencies), `methods/` (`q` pick, `r` router, `u` frequencies only, `p` longest units), `sources/` (cross-source comparison), `pron/` and `dialect/` (pronunciations and regions).
- `scripts/` entry points, `data/gold` and `data/samples` hand-made answers and judged samples (verdicts belong to the answer they were given for), `web/` viewer, `notes/` findings.
- Earlier experiments (methods a to o, local Llama) were removed from the code; their results remain in the viewer's History.

## Common commands

```
make live NAME=r-run ARGS="--method r --gold diagnostic --batch 100 --catalog --scheme grapheme"
make bank-align      whole-bank Jev run, about $0.4, progress bar
make bank-pron       free pronunciation methods on the whole bank
make sources         cross-source comparison (free, about a minute)
make m2m             unsupervised aligner over the dictionary
make free-results    free-method runs for the diagnostic and random sets
python3 scripts/build_em.py    rebuild learned frequencies after changing units or pool rules
```

Findings: `notes/FINDINGS.md`. Gold rulings: `notes/gold-decisions.md`. Viewer design: `notes/design-system.md`.

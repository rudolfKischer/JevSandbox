PY = python3 -I

test:
	$(PY) -m unittest discover -s tests

data:
	python3 scripts/data_bucket.py fetch

serve: data
	python3 scripts/serve.py

notation:
	$(PY) scripts/build_notation.py

baseline: data
	$(PY) scripts/run_experiment.py baseline-starter --method baseline

dry:
	$(PY) scripts/run_experiment.py dry-starter

live:
	$(PY) scripts/run_experiment.py $(NAME) --live $(ARGS)

bank-align:
	python3 -I scripts/run_big_set.py bank-route --live

bank-pron:
	python3 -I scripts/run_pron_big.py

sources:
	python3 -I scripts/compare_sources.py

m2m:
	python3 -I scripts/build_m2m.py

free-results: data
	$(PY) scripts/run_experiment.py u-diagnostic --method u --gold diagnostic --live --scheme grapheme
	$(PY) scripts/run_experiment.py p-diagnostic --method p --gold diagnostic --live --scheme grapheme
	$(PY) scripts/run_experiment.py u-random900 --method u --gold heldout+heldout2+heldout3 --live --scheme grapheme
	$(PY) scripts/run_experiment.py p-random900 --method p --gold heldout+heldout2+heldout3 --live --scheme grapheme

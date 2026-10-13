# PiML check (working paper plan §14.4, D27)

Required before the paper says anything about XGB2 as implemented in PiML, the toolbox Agus Sudjianto co-created.
Two questions on one dataset (`syn-none-n50000-s1`, level "none"):

1. Does our XGB2 decomposition (`src/verifier_gate/facts/xgb2.py`) agree with PiML's on the same fitted model?
2. Does PiML's XGB2 also fit the utilization × delinquencies pair that our XGB2 fits where none is planted?

Protocol, conventions and pass rules were written into the plan before the check dataset was touched; conventions
were established on the exploration dataset `syn-none-n5000-s1`.

## Environments

PiML 0.6.0.post2 needs Python ≤ 3.10 and old numpy/pandas/scikit-learn, so it has its own environment here, outside
the project's lock file. Its decomposition is only right for trees grown with `tree_method="exact"`, and on
xgboost ≥ 2.0 its default `tree_method="auto"` means `hist` (see findings), so the environment pins xgboost 1.7.6.

```
uv venv piml_check/.venv.nosync --python 3.10
uv pip install --python piml_check/.venv.nosync/bin/python "PiML==0.6.0.post2" "xgboost==1.7.6"
```

## Run (seconds)

```
uv run python piml_check/export_data.py syn-none-n50000-s1                  # project env: data + our rounds
piml_check/.venv.nosync/bin/python piml_check/fit_piml.py syn-none-n50000-s1 # PiML env: 3 fits, PiML's effects
uv run python piml_check/compare.py syn-none-n50000-s1                      # project env: criteria, summary
```

Fits: (a) PiML's defaults (100 trees, learning rate 0.3, `reg_lambda` 0); (b) our settings with `tree_method="exact"`
(380 rounds as our early stopping chose, learning rate 0.05, `reg_lambda` 1); (c) the same with `hist`, judged
through our decomposition only.

## Result (13 Oct 2026)

| | (a) PiML defaults | (b) our settings, exact | (c) our settings, hist |
|---|---|---|---|
| Our terms vs the booster's own leaves | 3e-15 | 3e-15 | 3e-15 |
| Ours vs PiML, data-weighted purification, largest difference | 0.0011 logits | 0.0011 logits | (PiML wrong for hist) |
| Ours vs PiML, uniform purification (PiML's default) | 0.0 | 0.0 | |
| Pair share, our measure (data-weighted) | 1.6%, largest pair | 1.1%, largest pair | 1.1%, largest pair |
| Pair rank on PiML's default importance | 16 of 33 | 6 of 36 | |

Our own XGB2 on the same data: 1.2%, largest pair.

- **Question 1: passed.** The decompositions agree under either purification convention.
- **Question 2: by the rule fixed in advance, PiML does not show the pair** (not in its top 3 by its own importance).
  The fitted boosters do contain it, at the size of ours. What hides it is PiML's default purification with uniform
  weights over grid cells:

| Purification | Measure | Pair rank, fit (a) | Pair rank, fit (b) |
|---|---|---|---|
| uniform cells (PiML default) | variance share (PiML's) | 16 of 33 | 6 of 36 |
| uniform cells | mean \|score\| share (ours) | 15 of 33 | 7 of 36 |
| data weights (`true_to_data=True`, ours) | variance share | 2 of 33 | 2 of 36 |
| data weights | mean \|score\| share | 1 of 33 | 1 of 36 |

## Side findings (for Agus, as a constructive note with a minimal reproduction)

- PiML's XGB2 decomposition reproduces the model's margin only for `tree_method="exact"`. For `hist` and `approx` it
  is off by up to 1.2–1.4 logits, about 0.3 logits even away from split values, on xgboost 1.7.6, 2.0.3 and 3.2.0
  (exploration dataset). Since xgboost 2.0, `tree_method="auto"` means `hist`, so PiML's defaults give wrong effects
  on any current xgboost, without a warning. PiML's requirement (`xgboost>=1.4.2`) allows these versions.
- PiML's default view purifies pairs with uniform weights over the grid cells; `true_to_data=True` uses the data's
  weights. The two conventions rank interactions differently (table above).
- Effect importance in PiML is each effect's variance share on the data.

## Files

`export_data.py`, `fit_piml.py`, `compare.py`; `data/` (not tracked); `results/<scenario>/`: boosters
(`*_booster.json`), PiML's effects per row (`*.npz`), agreement tables (`*_agreement_*.csv`), `piml_meta.json`,
`comparison.json`.

# PiML check (plan §14.4, D27; see `docs/decisions.md`)

Required before the paper says anything about XGB2 as implemented in PiML.
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
  The fitted boosters do contain it, at the size of ours, and PiML lists it; its default view only ranks it low.
  The reason is PiML's default purification with uniform weights over grid cells. The pair keeps roughly its size
  (fit (b): 1.13% data-weighted, 1.08% uniform); the other, spurious pairs grow under uniform weights, because they
  keep main-effect parts relative to the data, so the pair slips down the ranking. With `true_to_data=True`, PiML's
  own importance ranks it 2nd, so this is a default setting, not PiML ignoring the pair:

| Purification | Measure | Pair rank, fit (a) | Pair rank, fit (b) |
|---|---|---|---|
| uniform cells (PiML default) | variance share (PiML's) | 16 of 33 | 6 of 36 |
| uniform cells | mean \|score\| share (ours) | 15 of 33 | 7 of 36 |
| data weights (`true_to_data=True`, ours) | variance share | 2 of 33 | 2 of 36 |
| data weights | mean \|score\| share | 1 of 33 | 1 of 36 |

## Side findings (to be reported to PiML's maintainers, with a minimal reproduction)

- PiML's XGB2 decomposition reproduces the model's margin only for `tree_method="exact"`. For `hist` and `approx` it
  misroutes training rows that sit on a split value (narrowed by the toy check below; the 13 Oct reading, "about
  0.3 logits even away from split values", did not reproduce on toy data). Since xgboost 2.0, `tree_method="auto"`
  means `hist`, so PiML's defaults are affected on any current xgboost, without a warning. PiML's requirement
  (`xgboost>=1.4.2`) allows these versions.
- PiML's default view purifies pairs with uniform weights over the grid cells; `true_to_data=True` uses the data's
  weights. The two conventions rank interactions differently (table above).
- Effect importance in PiML is each effect's variance share on the data.

## Toy check of the hist/approx finding (14 Oct 2026, D28)

Before the finding is reported, it was reproduced on a toy dataset outside our benchmark, with PiML's own API for the
outcome (`toy_hist.py`; rule fixed in the script before the run). Toy: 3 features uniform on [0, 1], n = 2,000,
logit 2 x1 − 1.5 x2 + 4 (x1 − 0.5)(x3 − 0.5). The margin is rebuilt from `parse_model()` (intercept + main effects +
interactions, PiML's raw outputs) and compared with `decision_function`.

| xgboost | tree_method | Largest gap, training rows | Rows away from split values | Fresh rows | `split_calibration=True` |
|---|---|---|---|---|---|
| 1.7.6 | exact (= defaults) | 1e-5 | 1e-5 | 1e-5 | 1e-5 |
| 1.7.6 | hist | 0.96 | 0.002 | 0.002 | 0.002 |
| 1.7.6 | approx | 1.33 | 3e-5 | 3e-5 | 7e-5 |
| 2.0.3 | defaults (auto → hist) | 0.99 | 0.001 | 0.001 | 0.001 |
| 2.0.3 | exact | 8e-6 | 8e-6 | 9e-6 | 8e-6 |
| 2.0.3 | approx | 0.75 | 0.001 | 0.001 | 0.001 |

**Outcome by the rule: not reproduced as written.** Exact trees are right, and hist/approx trees are wrong by up to
1–1.3 logits, but only on rows that sit on a split value: away from the splits and on fresh rows the gap is 0.001–0.002
logits (below the rule's 0.05). The 13 Oct statement ("about 0.3 logits even away from split values") is withdrawn.

**Characterisation, formed after the result** (`toy_hist_followup.py`, both xgboost versions):

- Continuous features: 3.5–5.5% of training rows are off by more than 0.05 logits, all of them on a split value.
- With one count feature (Poisson, clipped at 6), as credit data have (delinquencies, inquiries): 82–88% of training
  rows are off by more than 0.05 logits, median 0.2, largest 1.8–2.3. hist and approx put splits on the integer
  values, so most rows sit on a split; three quarters of the off rows are on one, the rest is not explained here.
- PiML's `XGBInterpreter` has an undocumented option, `split_calibration` (default False). Read with our evaluator, it
  repairs the continuous toy (largest gap 0.001–0.002); on the count toy it removes the misrouting but leaves a
  constant offset of 0.32 logits on every row that we have not explained. `parse_model()`, what users get, does not
  expose it.

**What the evidence supports** (with `toy_hist.py` as the reproduction): on hist and approx trees,
PiML's XGB2 effects misroute training rows that lie on split values, by up to about 1 logit (continuous features) and
2 logits (count features, where most rows are affected); exact trees are right; the default `auto` means hist from
xgboost 2.0 on; `split_calibration` looks like the intended fix and could be the default. What it does not support:
that the effects are wrong away from split values, or anything about the 0.32 offset before it is understood.

Run (seconds): `piml_check/.venv.nosync/bin/python piml_check/toy_hist.py` and `toy_hist_followup.py`; for xgboost
2.0.3, the same in an environment with `PiML==0.6.0.post2` and `xgboost==2.0.3`. Results: `results/toy_hist/`.

## Files

`export_data.py`, `fit_piml.py`, `compare.py`, `toy_hist.py`, `toy_hist_followup.py`; `data/` (not tracked); `results/<scenario>/`: boosters
(`*_booster.json`), PiML's effects per row (`*.npz`), agreement tables (`*_agreement_*.csv`), `piml_meta.json`,
`comparison.json`.

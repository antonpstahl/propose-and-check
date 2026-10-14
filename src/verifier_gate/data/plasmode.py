"""Plasmode tier (plan §4.4): real TaiwanCredit features, a planted outcome.

Source: UCI "Default of Credit Card Clients" (id 350; Yeh 2009; CC BY 4.0, DOI 10.24432/C55S3H): 30,000 credit
card clients, default rate 22.1%. `fetch` downloads it once into data/raw/ and checks its hash. SEX and MARRIAGE
are dropped, as a lender would (ECOA).

The planted truth mirrors the synthetic tier role for role (data/dgp.py), with the same target shares, so every
planted share sits at least 0.8 points inside its lexicon class at every interaction level:

| feature   | role            | share | planted shape                                                                     |
|-----------|-----------------|-------|-----------------------------------------------------------------------------------|
| PAY_0     | strong          | 0.40  | the real-label EBM's, per status value; monotone from 0 up, -2 and -1 as fitted   |
| LIMIT_BAL | strong          | 0.24  | the real-label EBM's, made monotone (decreasing) and smooth                        |
| BILL_AMT1 | moderate        | 0.13  | the bill effect (the EBM puts it on BILL_AMT2), monotone (increasing) and smooth   |
| PAY_AMT1  | moderate        | 0.10  | the real-label EBM's, monotone (decreasing) and smooth                             |
| PAY_AMT2  | threshold       | 0.08  | a sharp step down at 2,000                                                        |
| AGE       | weak            | 0.04  | the real-label EBM's, monotone (increasing) and smooth                             |
| EDUCATION | near flat       | 0.01  | linear in the code, clipped to 1 (graduate school) to 3 (high school)              |
| BILL_AMT2 | correlated null | 0     | zero; Spearman 0.91 with BILL_AMT1, so a model can move the effect onto it          |
| PAY_AMT3  | noise           | 0     | zero                                                                              |

PAY_0 keeps its real shape: risk is lowest at 0 (revolving) and higher at -2 and -1 (no use, paid in full), on
about 28% of the rows. So "increases" and "mostly increases" are clearly false for the strongest feature, a case
the synthetic tier does not have. Shapes are smoothed (monotone, then shape-preserving interpolation) so the
real-label EBM's noise is not planted (§11).

Pairs, on nearly independent features (Spearman 0.13 and 0.00), so they are close to pure; T is defined as
written, not purified, and pairs are compared by pattern (§4.4):
- amplification, PAY_0 & EDUCATION: late payment raises risk more for applicants with high-school or other
  education (EDUCATION >= 3): c * (f_PAY_0 - mean) * (1{EDUCATION >= 3} - share);
- sign flip, AGE & BILL_AMT1: age raises risk for small bills and lowers it for large ones:
  c * (AGE - mean) * (g(BILL_AMT1) - mean), g = -asinh(BILL_AMT1 / 20,000).
Shares by level as in the synthetic tier: none 0 / 0, weak 3% / 6%, dominant 21% / 6%.

The population is the full 30,000 rows: shapes are centred on it, coefficients set the target shares on it, and
b0 sets its default rate to 22%. Datasets: interaction level x n (5,000 or all 30,000) x seed (1-3). Within a
seed the rows come in one random order, n = 5,000 takes the first 5,000, and the uniforms that decide y are
shared across levels (common random numbers), as in the synthetic tier. Seed 1 is never used for calibration
here: the plasmode tier is a pure out-of-sample test of the frozen lexicon (§4.4).
"""

import hashlib
import json
import urllib.request
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from scipy.special import expit

URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
ZIP_SHA256 = "56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602"
XLS_SHA256 = "30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933"
RAW = Path(__file__).parents[3] / "data" / "raw"
XLS = RAW / "taiwan_credit.xls"
SHAPES = Path(__file__).with_name("plasmode_shapes.json")  # the planted shapes, derived once and kept

FEATURES = ("PAY_0", "LIMIT_BAL", "BILL_AMT1", "PAY_AMT1", "PAY_AMT2", "AGE", "EDUCATION", "BILL_AMT2", "PAY_AMT3")
INTERACTION_LEVELS = ("none", "weak", "dominant")
SAMPLE_SIZES = (5_000, 30_000)
SEEDS = (1, 2, 3)
BASE_RATE = 0.22
TOTAL_MAIN_IMPORTANCE = 1.6
MAIN_SHARES = {"PAY_0": 0.40, "LIMIT_BAL": 0.24, "BILL_AMT1": 0.13, "PAY_AMT1": 0.10, "PAY_AMT2": 0.08, "AGE": 0.04,
               "EDUCATION": 0.01, "BILL_AMT2": 0.0, "PAY_AMT3": 0.0}  # fmt: skip
AMPLIFICATION = "PAY_0 & EDUCATION"
SIGN_FLIP = "AGE & BILL_AMT1"
PAIR_SHARES = {
    "none": {AMPLIFICATION: 0.0, SIGN_FLIP: 0.0},
    "weak": {AMPLIFICATION: 0.03, SIGN_FLIP: 0.06},
    "dominant": {AMPLIFICATION: 0.21, SIGN_FLIP: 0.06},
}
PAIR_PATTERNS = {AMPLIFICATION: "amplification", SIGN_FLIP: "sign_flip"}
FEATURE_ROLES = {"PAY_0": "strong", "LIMIT_BAL": "strong", "BILL_AMT1": "moderate", "PAY_AMT1": "moderate",
                 "PAY_AMT2": "threshold", "AGE": "weak", "EDUCATION": "near_flat", "BILL_AMT2": "correlated_null",
                 "PAY_AMT3": "noise"}  # fmt: skip
STEP_AT = 2_000.0  # PAY_AMT2
BILL_SCALE = 20_000.0
EBM_PARAMS = {"interactions": 0, "max_bins": 256, "random_state": 0}  # shape discovery on the real label


# --- the data ----------------------------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch() -> Path:
    """Download the UCI file once into data/raw/ and check both hashes."""
    if XLS.exists() and _sha256(XLS) == XLS_SHA256:
        return XLS
    RAW.mkdir(parents=True, exist_ok=True)
    archive = RAW / "taiwan_credit.zip"
    if not archive.exists() or _sha256(archive) != ZIP_SHA256:
        urllib.request.urlretrieve(URL, archive)
    if _sha256(archive) != ZIP_SHA256:
        raise RuntimeError("the downloaded archive does not match the recorded hash")
    with zipfile.ZipFile(archive) as z:
        XLS.write_bytes(z.read("default of credit card clients.xls"))
    if _sha256(XLS) != XLS_SHA256:
        raise RuntimeError("the extracted file does not match the recorded hash")
    return XLS


@cache
def taiwan() -> pd.DataFrame:
    """The 30,000 clients: the 9 features of the tier as floats and the real label `default`."""
    raw = pd.read_excel(fetch(), header=1)
    out = raw[list(FEATURES)].astype(np.float64)
    out["default"] = raw["default payment next month"].astype(np.int64)
    return out


# --- the planted shapes ------------------------------------------------------------------------------------


def _bins(values: np.ndarray, cuts: np.ndarray) -> np.ndarray:
    return np.searchsorted(cuts, values, side="right")  # x == cut belongs to the upper bin (facts/steps.py)


def _monotone(x: np.ndarray, scores: np.ndarray, weights: np.ndarray, increasing: bool) -> dict:
    """Weighted isotonic fit over the bins, then knots at the middle of each constant run (and both ends) for
    shape-preserving interpolation: monotone and smooth."""
    from sklearn.isotonic import IsotonicRegression

    fitted = IsotonicRegression(increasing=increasing).fit(x, scores, sample_weight=weights).predict(x)
    runs = np.split(np.arange(len(x)), np.flatnonzero(np.diff(fitted) != 0) + 1)
    knots_x = [x[0]] + [float(np.average(x[r], weights=weights[r])) for r in runs] + [x[-1]]
    knots_y = [fitted[0]] + [float(fitted[r[0]]) for r in runs] + [fitted[-1]]
    keep = np.concatenate([[True], np.diff(knots_x) > 0])
    return {"kind": "pchip", "x": list(np.asarray(knots_x)[keep]), "y": list(np.asarray(knots_y)[keep])}


def derive_shapes() -> dict:
    """Fit an EBM on the real label (main effects only) and turn its terms into the planted shapes. Run once;
    the result is kept in plasmode_shapes.json, which is the planted truth as written down."""
    from interpret import __version__ as interpret_version
    from interpret.glassbox import ExplainableBoostingClassifier

    data = taiwan()
    X, y = data[list(FEATURES)], data["default"].to_numpy()
    ebm = ExplainableBoostingClassifier(**EBM_PARAMS).fit(X, y)
    fitted = {}
    for i, name in enumerate(ebm.term_names_):
        cuts = np.asarray(ebm.bins_[i][0], dtype=np.float64)
        scores = np.asarray(ebm.term_scores_[i][1:-1], dtype=np.float64)
        bins = _bins(X[name].to_numpy(), cuts)
        held = np.bincount(bins, minlength=len(scores)).astype(np.float64)
        x = np.array([X[name].to_numpy()[bins == b].mean() if held[b] else np.nan for b in range(len(scores))])
        ok = held > 0
        fitted[name] = (x[ok], scores[ok], held[ok])

    shapes = {}
    x, s, w = fitted["PAY_0"]  # per status value: -2 and -1 as fitted, monotone from 0 up
    low, high = x < 0, x >= 0
    upper = _monotone(x[high], s[high], w[high], increasing=True)
    values = np.concatenate([s[low], np.interp(x[high], upper["x"], upper["y"])])
    shapes["PAY_0"] = {"kind": "table", "x": list(x), "y": list(values)}
    shapes["LIMIT_BAL"] = _monotone(*fitted["LIMIT_BAL"], increasing=False)
    shapes["BILL_AMT1"] = _monotone(*fitted["BILL_AMT2"], increasing=True)  # the bill effect, on BILL_AMT1
    shapes["PAY_AMT1"] = _monotone(*fitted["PAY_AMT1"], increasing=False)
    shapes["PAY_AMT2"] = {"kind": "step", "at": STEP_AT, "sign": -1.0}
    shapes["AGE"] = _monotone(*fitted["AGE"], increasing=True)
    shapes["EDUCATION"] = {"kind": "clip", "lo": 1.0, "hi": 3.0}
    shapes["BILL_AMT2"] = shapes["PAY_AMT3"] = {"kind": "zero"}
    meta = {"source": "UCI 350, xls sha256 " + XLS_SHA256, "ebm": EBM_PARAMS, "interpret": interpret_version}
    return {"meta": meta, "shapes": shapes}


def write_shapes() -> dict:
    spec = derive_shapes()
    SHAPES.write_text(json.dumps(spec, indent=1) + "\n")
    for cached in (_spec, shape, _population, coefficients, base_intercept):
        cached.cache_clear()
    return spec


@cache
def _spec() -> dict:
    return json.loads(SHAPES.read_text())["shapes"]


@cache
def shape(feature: str) -> Callable[[np.ndarray], np.ndarray]:
    s = _spec()[feature]
    if s["kind"] == "zero":
        return lambda v: np.zeros_like(v)
    if s["kind"] == "step":
        return lambda v: s["sign"] * (v >= s["at"]).astype(np.float64)
    if s["kind"] == "clip":
        return lambda v: np.clip(v, s["lo"], s["hi"])
    xs, ys = np.asarray(s["x"]), np.asarray(s["y"])
    if s["kind"] == "table":
        return lambda v: np.interp(v, xs, ys)
    curve = PchipInterpolator(xs, ys, extrapolate=False)
    return lambda v: curve(np.clip(v, xs[0], xs[-1]))


def _education_factor(v):
    return (v >= 3).astype(np.float64)


def _bill_factor(v):
    return -np.arcsinh(v / BILL_SCALE)


def _identity(v):
    return v


def _pair_factors() -> dict[str, tuple[tuple[str, str], tuple[Callable, Callable]]]:
    return {
        AMPLIFICATION: (("PAY_0", "EDUCATION"), (shape("PAY_0"), _education_factor)),
        SIGN_FLIP: (("AGE", "BILL_AMT1"), (_identity, _bill_factor)),
    }


TERMS = FEATURES + (AMPLIFICATION, SIGN_FLIP)


def term_features(name: str) -> tuple[str, ...]:
    return (name,) if name in FEATURES else _pair_factors()[name][0]


def _column(X: Mapping, feature: str) -> np.ndarray:
    return np.asarray(X[feature], dtype=np.float64)


@cache
def _population() -> tuple[dict, dict]:
    """Population means of the unit shapes and pair factors, and importances of the centred unit terms."""
    ref = taiwan()
    means, importances = {}, {}
    for feature in FEATURES:
        values = shape(feature)(_column(ref, feature))
        means[feature] = float(values.mean())
        importances[feature] = float(np.abs(values - values.mean()).mean())
    for name, ((a, b), (fa, fb)) in _pair_factors().items():
        va, vb = fa(_column(ref, a)), fb(_column(ref, b))
        means[name] = (float(va.mean()), float(vb.mean()))
        importances[name] = float(np.abs((va - va.mean()) * (vb - vb.mean())).mean())
    return means, importances


def unit_term(name: str, X: Mapping) -> np.ndarray:
    """Unit shape of a term centred on the population (coefficient 1)."""
    means, _ = _population()
    if name in FEATURES:
        return shape(name)(_column(X, name)) - means[name]
    (a, b), (fa, fb) = _pair_factors()[name]
    ma, mb = means[name]
    return (fa(_column(X, a)) - ma) * (fb(_column(X, b)) - mb)


@cache
def coefficients(interaction: str) -> dict[str, float]:
    _, importances = _population()
    coef = {f: MAIN_SHARES[f] * TOTAL_MAIN_IMPORTANCE / importances[f] if MAIN_SHARES[f] else 0.0 for f in FEATURES}
    pair_shares = PAIR_SHARES[interaction]
    total = TOTAL_MAIN_IMPORTANCE / (1.0 - sum(pair_shares.values()))
    for name, share in pair_shares.items():
        coef[name] = share * total / importances[name]
    return coef


def _population_term(name: str, X: Mapping, interaction: str) -> np.ndarray:
    return coefficients(interaction)[name] * unit_term(name, X)


@cache
def base_intercept(interaction: str) -> float:
    ref = taiwan()
    eta = sum(_population_term(t, ref, interaction) for t in TERMS)
    return float(brentq(lambda b0: expit(b0 + eta).mean() - BASE_RATE, -20.0, 20.0, xtol=1e-12))


# --- truth, scenarios, datasets ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Truth:
    """Planted truth T, every term centred on the training sample (as data/dgp.py's Truth)."""

    interaction: str
    intercept: float
    offsets: Mapping[str, float]
    features = FEATURES

    @property
    def term_names(self) -> tuple[str, ...]:
        return TERMS

    def term_features(self, name: str) -> tuple[str, ...]:
        return term_features(name)

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return _population_term(name, X, self.interaction) - self.offsets[name]

    def terms(self, X: Mapping) -> dict[str, np.ndarray]:
        return {name: self.term(name, X) for name in TERMS}

    def logit(self, X: Mapping) -> np.ndarray:
        return self.intercept + sum(self.terms(X).values())

    def importances(self, X: Mapping) -> dict[str, float]:
        return {name: float(np.abs(values).mean()) for name, values in self.terms(X).items()}

    def shares(self, X: Mapping) -> dict[str, float]:
        importances = self.importances(X)
        total = sum(importances.values())
        return {name: value / total for name, value in importances.items()}


@dataclass(frozen=True)
class Scenario:
    interaction: str
    n: int
    seed: int
    tier = "plasmode"

    @property
    def id(self) -> str:
        return f"pls-{self.interaction}-n{self.n}-s{self.seed}"

    @property
    def is_discovery(self) -> bool:
        return False  # never used for calibration (§4.4)


SCENARIOS = tuple(Scenario(i, n, s) for i in INTERACTION_LEVELS for n in SAMPLE_SIZES for s in SEEDS)


@dataclass(frozen=True)
class Dataset:
    scenario: Scenario
    X: pd.DataFrame
    y: np.ndarray
    truth: Truth


def make_truth(X: Mapping, interaction: str) -> Truth:
    offsets = {name: float(_population_term(name, X, interaction).mean()) for name in TERMS}
    return Truth(interaction, base_intercept(interaction) + sum(offsets.values()), offsets)


def generate(scenario: Scenario) -> Dataset:
    rng = np.random.default_rng([17, scenario.seed])
    data = taiwan()
    order = rng.permutation(len(data))
    uniforms = rng.uniform(size=len(data))[: scenario.n]
    X = data.iloc[order[: scenario.n]][list(FEATURES)].reset_index(drop=True)
    truth = make_truth(X, scenario.interaction)
    y = (uniforms < expit(truth.logit(X))).astype(np.int64)
    return Dataset(scenario, X, y, truth)


def save(path: Path = Path(__file__).parents[3] / "data" / "plasmode") -> list[Path]:
    """The 18 datasets as CSV (features, planted y, and T's logit for reference); regenerated from the seeds."""
    path.mkdir(parents=True, exist_ok=True)
    out = []
    for scenario in SCENARIOS:
        d = generate(scenario)
        frame = d.X.assign(y=d.y, planted_logit=d.truth.logit(d.X))
        target = path / f"{scenario.id}.csv.gz"
        frame.to_csv(target, index=False)
        out.append(target)
    return out


EDGES = (0.02, 0.05, 0.15)  # the lexicon's class edges (lexicon.yaml)
NEAR = 0.005  # report planted shares within half a point of an edge (§14.14), never tune them away


def edge_report() -> pd.DataFrame:
    """Each dataset's planted shares (T on the sample) and their distance to the nearest class edge."""
    rows = []
    for scenario in SCENARIOS:
        d = generate(scenario)
        for term, share in d.truth.shares(d.X).items():
            if share > 0:
                distance = min(abs(share - e) for e in EDGES)
                rows.append({"scenario": scenario.id, "term": term, "share": share, "to nearest edge": distance, "near": distance < NEAR})
    return pd.DataFrame(rows)


def main() -> None:
    """Fetch the data, write the 18 datasets to data/plasmode/, and report planted shares near a class edge."""
    fetch()
    if not SHAPES.exists():
        write_shapes()
    paths = save()
    report = edge_report()
    print(f"{len(paths)} datasets in {paths[0].parent}")
    print(f"Planted shares within {NEAR:.1%} of a class edge: {int(report.near.sum())} of {len(report)}")
    closest = report.sort_values("to nearest edge").head(8)
    print(closest.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

"""Analyse the e-mail experiment end to end.

    make run                 on data/hillstrom.csv
    make smoke               on synthetic data with known effects (pipeline check)

Steps, in the order a careful analyst would take them:
  1. Is the experiment sound? Sample-ratio mismatch and covariate balance.
  2. What did each e-mail do? Visit, conversion and spend vs no e-mail, with
     confidence intervals and Holm-adjusted p-values (6 comparisons).
  3. Was it big enough? The minimum detectable lift for conversion.
  4. For whom? Uplift models trained on half the data, judged on the other half.
Writes results.json, an effects plot and a Qini plot per e-mail to --out;
scripts/report.py then renders RESULTS.md from results.json.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from abtest import data as d  # noqa: E402
from abtest import stats as st  # noqa: E402
from abtest import uplift as u  # noqa: E402

TARGET_SHARES = (0.1, 0.3, 0.5)
PERMUTATIONS = 1000


def check_experiment(df) -> dict:
    counts = [int((df["segment"] == arm).sum()) for arm in d.ARMS]
    balance = {}
    control = df[df["segment"] == d.CONTROL]
    for arm in d.ARMS[1:]:
        treated = df[df["segment"] == arm]
        balance[arm] = {
            c: st.standardised_mean_difference(treated[c], control[c]) for c in d.COVARIATES
        }
    worst = max(abs(v) for arm in balance.values() for v in arm.values())
    return {
        "arm_sizes": dict(zip(d.ARMS, counts, strict=True)),
        "sample_ratio_mismatch_p": st.sample_ratio_mismatch(counts, [1 / 3] * 3),
        "standardised_mean_differences": balance,
        "worst_abs_smd": worst,
        "balanced": worst < 0.1,
    }


def effects(df) -> dict:
    control = df[df["segment"] == d.CONTROL]
    out, p_values, keys = {}, [], []
    for arm in d.ARMS[1:]:
        treated = df[df["segment"] == arm]
        out[arm] = {}
        for outcome in d.OUTCOMES:
            if outcome == "spend":
                c = st.compare_means(treated[outcome], control[outcome])
            else:
                c = st.compare_proportions(
                    int(treated[outcome].sum()),
                    len(treated),
                    int(control[outcome].sum()),
                    len(control),
                )
            out[arm][outcome] = asdict(c)
            p_values.append(c.p_value)
            keys.append((arm, outcome))
    for (arm, outcome), adjusted in zip(keys, st.holm(p_values), strict=True):
        out[arm][outcome]["p_value_holm"] = adjusted
    return out


def power(df) -> dict:
    control = df[df["segment"] == d.CONTROL]
    n = int(min((df["segment"] == arm).sum() for arm in d.ARMS))
    rate = float(control["conversion"].mean())
    mde = st.minimum_detectable_lift(rate, n)
    return {
        "control_conversion": rate,
        "customers_per_arm": n,
        "minimum_detectable_absolute_lift": mde,
        "minimum_detectable_relative_lift": mde / rate if rate else None,
    }


def uplift(df, arm: str, seed: int = 7) -> tuple[dict, dict]:
    sub = df[df["segment"].isin([arm, d.CONTROL])].reset_index(drop=True)
    X, names = d.model_matrix(sub)
    t = (sub["segment"] == arm).to_numpy()
    y = sub["conversion"].to_numpy()
    idx_train, idx_test = train_test_split(
        np.arange(len(sub)), test_size=0.5, random_state=seed, stratify=t * 2 + y
    )
    models = {
        "logistic T-learner": LogisticRegression(max_iter=2000),
        "gradient boosting T-learner": HistGradientBoostingClassifier(
            max_depth=3, learning_rate=0.05, max_iter=200, random_state=seed
        ),
    }
    result, curves = {}, {}
    for name, base in models.items():
        model = u.TLearner(base).fit(X[idx_train], t[idx_train], y[idx_train])
        scores = model.predict_uplift(X[idx_test])
        result[name] = {
            "qini_coefficient_test": u.qini_coefficient(scores, t[idx_test], y[idx_test]),
            # How often a random ranking of the same customers scores at least
            # as high: is the curve above random by more than chance?
            "qini_permutation_p": u.qini_permutation_p(
                scores, t[idx_test], y[idx_test], n=PERMUTATIONS
            ),
            "targeting": [
                u.targeting_value(scores, t[idx_test], y[idx_test], s) for s in TARGET_SHARES
            ],
        }
        curves[name] = u.qini_curve(scores, t[idx_test], y[idx_test])
    return {
        "arm": arm,
        "test_customers": len(idx_test),
        "qini_permutations": PERMUTATIONS,
        "models": result,
    }, curves


def plot_effects(eff: dict, path: Path, source: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, outcome in zip(axes, d.OUTCOMES, strict=True):
        for i, arm in enumerate(d.ARMS[1:]):
            c = eff[arm][outcome]
            ax.errorbar(
                [i],
                [c["difference"]],
                yerr=[[c["difference"] - c["ci_low"]], [c["ci_high"] - c["difference"]]],
                fmt="o",
                capsize=6,
            )
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_xticks([0, 1], ["Men's e-mail", "Women's e-mail"])
        ax.set_title(f"{outcome}: e-mail minus no e-mail")
        if outcome != "spend":
            ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    fig.suptitle(f"Effect of each e-mail with 95% confidence intervals ({source})")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_qini(curves: dict, path: Path, arm: str, source: str) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for name, (share, gain) in curves.items():
        ax.plot(share, gain, label=name)
    share, gain = next(iter(curves.values()))
    ax.plot([0, 1], [0, gain[-1]], "k--", label="random targeting")
    ax.set_xlabel("Share of customers targeted (highest predicted uplift first)")
    ax.set_ylabel("Incremental conversions")
    ax.set_title(f"Qini curve, held-out half: {arm} ({source})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/hillstrom.csv")
    parser.add_argument("--synthetic", action="store_true", help="use synthetic data instead")
    parser.add_argument("--out", default="evidence")
    args = parser.parse_args()

    df = d.synthetic() if args.synthetic else d.load(args.data)
    source = "synthetic data" if args.synthetic else Path(args.data).name
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    experiment = check_experiment(df)
    eff = effects(df)
    pw = power(df)
    upl = {}
    for arm in d.ARMS[1:]:
        upl[arm], curves = uplift(df, arm)
        plot_qini(curves, out / f"qini_{arm.split()[0].lower()}.png", arm, source)
    plot_effects(eff, out / "effects.png", source)

    results = {
        "data": "synthetic (pipeline check)" if args.synthetic else args.data,
        "customers": len(df),
        "experiment_checks": experiment,
        "effects": eff,
        "power": pw,
        "uplift": upl,
    }
    # allow_nan=False: an undefined value (e.g. a lift over a zero control rate)
    # is written as null, never as NaN, which is not valid JSON.
    (out / "results.json").write_text(
        json.dumps(json_safe(results), indent=2, allow_nan=False) + "\n"
    )
    print(json.dumps(json_safe({"checks": experiment, "power": pw}), indent=2))
    return 0


def json_safe(value):
    """Plain JSON types: NumPy scalars unwrapped, NaN and infinity as None."""
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


if __name__ == "__main__":
    sys.exit(main())

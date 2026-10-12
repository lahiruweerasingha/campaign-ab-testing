"""Edge cases: undefined statistics, invalid input files, and the report's handling of both."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

from abtest import data as d
from abtest import uplift as u

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_analysis = _load("run_analysis")
report = _load("report")


def test_permutation_p_is_undefined_when_the_qini_is():
    # No conversions at all: total incremental gain is 0, so the Qini
    # coefficient is undefined, and so is its p-value (not "significant").
    scores = np.arange(10.0)
    treated = np.array([1, 0] * 5)
    y = np.zeros(10)
    assert math.isnan(u.qini_coefficient(scores, treated, y))
    assert math.isnan(u.qini_permutation_p(scores, treated, y, n=50))


def test_json_safe_writes_valid_json():
    value = {"a": float("nan"), "b": [np.float64(1.5), np.int64(3), float("inf")], "c": None}
    safe = run_analysis.json_safe(value)
    assert safe == {"a": None, "b": [1.5, 3, None], "c": None}
    json.dumps(safe, allow_nan=False)  # raises if anything non-finite is left


def _minimal_results() -> dict:
    comparison = {
        "control_mean": 0.0,
        "treatment_mean": 0.01,
        "difference": 0.01,
        "ci_low": 0.0,
        "ci_high": 0.02,
        "relative_lift": None,  # lift over a zero control rate
        "p_value": 0.01,
        "p_value_holm": 0.03,
    }
    targeting = [
        {"share_targeted": s, "uplift_in_targeted": None, "uplift_overall": 0.01}
        for s in (0.2, 0.6)
    ]
    return {
        "data": "test",
        "customers": 100,
        "experiment_checks": {
            "arm_sizes": {"No E-Mail": 50, "Mens E-Mail": 50},
            "sample_ratio_mismatch_p": 1.0,
            "worst_abs_smd": 0.0,
            "balanced": True,
        },
        "effects": {"Mens E-Mail": {"conversion": comparison, "spend": comparison}},
        "power": {
            "control_conversion": 0.0,
            "customers_per_arm": 50,
            "minimum_detectable_absolute_lift": None,
            "minimum_detectable_relative_lift": None,
        },
        "uplift": {
            "Mens E-Mail": {
                "qini_permutations": 99,
                "models": {
                    "m": {
                        "qini_coefficient_test": None,
                        "qini_permutation_p": None,
                        "targeting": targeting,
                    }
                },
            }
        },
    }


def test_report_renders_undefined_values_and_any_target_shares(tmp_path):
    (tmp_path / "results.json").write_text(json.dumps(_minimal_results()))
    report.main(str(tmp_path))
    text = (tmp_path / "RESULTS.md").read_text(encoding="utf-8")
    assert "n/a" in text
    assert "nan" not in text.lower().replace("n/a", "")
    assert "Uplift if top 20% targeted" in text and "top 60%" in text
    assert "99 random rankings" in text


@pytest.mark.parametrize(
    ("column", "bad_value", "message"),
    [
        ("conversion", 2, "conversion must be 0/1"),
        ("spend", -1.0, "negative spend"),
        ("recency", np.nan, "missing values"),
    ],
)
def test_load_rejects_bad_values(tmp_path, column, bad_value, message):
    df = d.synthetic(200)
    df[column] = df[column].astype(float)
    df.loc[0, column] = bad_value
    path = tmp_path / "bad.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match=message):
        d.load(path)

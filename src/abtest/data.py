"""Loading and checking the Hillstrom e-mail experiment, plus a synthetic twin.

The Hillstrom (MineThatData, 2008) data: 64,000 customers who bought in the
last twelve months, randomly split into three equal arms: a men's merchandise
e-mail, a women's merchandise e-mail, or no e-mail. Outcomes over the next two
weeks: a site visit, a conversion (purchase), and spend.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ARMS = ("No E-Mail", "Mens E-Mail", "Womens E-Mail")
CONTROL = "No E-Mail"
OUTCOMES = ("visit", "conversion", "spend")
COLUMNS = (
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
)
# Pre-treatment covariates: known before the e-mail was sent.
COVARIATES = ("recency", "history", "mens", "womens", "newbie")
CATEGORICAL = {
    "zip_code": ("Surburban", "Urban", "Rural"),
    "channel": ("Phone", "Web", "Multichannel"),
}


def load(path: str | Path) -> pd.DataFrame:
    """Read the CSV and check it is the experiment it claims to be."""
    df = pd.read_csv(path)
    missing = sorted(set(COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"missing columns: {missing}")
    unknown = sorted(set(df["segment"]) - set(ARMS))
    if unknown:
        raise ValueError(f"unknown experiment arms: {unknown}")
    if df[list(COLUMNS)].isna().any().any():
        raise ValueError("missing values in the experiment data")
    for col in ("visit", "conversion"):
        if not set(df[col].unique()) <= {0, 1}:
            raise ValueError(f"{col} must be 0/1")
    if (df["spend"] < 0).any():
        raise ValueError("negative spend")
    return df


def model_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Numeric features for uplift models: covariates plus one-hot categories."""
    parts = [df[list(COVARIATES)].astype(float)]
    names = list(COVARIATES)
    for col, levels in CATEGORICAL.items():
        for level in levels[1:]:  # first level is the reference
            parts.append((df[col] == level).astype(float).rename(f"{col}={level}"))
            names.append(f"{col}={level}")
    return pd.concat(parts, axis=1).to_numpy(), names


def synthetic(n: int = 64_000, seed: int = 7) -> pd.DataFrame:
    """A randomised experiment with the Hillstrom schema and KNOWN effects.

    Used only to test the pipeline. The women's e-mail lifts conversion only
    for customers who bought women's merchandise before (`womens == 1`); the
    men's e-mail has a small effect for everyone.
    """
    rng = np.random.default_rng(seed)
    womens = rng.integers(0, 2, n)
    mens = np.where(womens == 1, rng.integers(0, 2, n), 1)
    history = np.round(rng.lognormal(5, 0.8, n), 2)
    df = pd.DataFrame(
        {
            "recency": rng.integers(1, 13, n),
            "history_segment": "1) $0 - $100",
            "history": history,
            "mens": mens,
            "womens": womens,
            "zip_code": rng.choice(CATEGORICAL["zip_code"], n),
            "newbie": rng.integers(0, 2, n),
            "channel": rng.choice(CATEGORICAL["channel"], n),
            "segment": rng.choice(ARMS, n),
        }
    )
    base = 0.006 + 0.002 * (df["recency"] < 4)
    lift = np.where(df["segment"] == "Mens E-Mail", 0.004, 0.0)
    lift = lift + np.where((df["segment"] == "Womens E-Mail") & (df["womens"] == 1), 0.012, 0.0)
    df["conversion"] = (rng.random(n) < base + lift).astype(int)
    df["visit"] = np.maximum(df["conversion"], (rng.random(n) < 0.10 + 5 * lift).astype(int))
    df["spend"] = np.where(df["conversion"] == 1, np.round(rng.gamma(2.0, 60.0, n), 2), 0.0)
    return df

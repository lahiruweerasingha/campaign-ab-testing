"""Statistics for comparing the arms of a randomised experiment.

Plain NumPy/SciPy so every formula can be checked by hand in the tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Comparison:
    """Treatment minus control for one outcome."""

    control_mean: float
    treatment_mean: float
    difference: float
    ci_low: float
    ci_high: float
    relative_lift: float
    p_value: float


def sample_ratio_mismatch(observed: list[int], expected_share: list[float]) -> float:
    """p-value of a chi-square test that the arm sizes match the intended split.

    A tiny p-value means assignment did not work as designed (a logging bug,
    a filter applied to one arm, a broken randomiser), and no effect estimate
    from the experiment can be trusted until that is explained.
    """
    observed_arr = np.asarray(observed, dtype=float)
    share = np.asarray(expected_share, dtype=float)
    if not math.isclose(share.sum(), 1.0):
        raise ValueError("expected shares must sum to 1")
    expected = observed_arr.sum() * share
    return float(stats.chisquare(observed_arr, expected).pvalue)


def standardised_mean_difference(treatment: np.ndarray, control: np.ndarray) -> float:
    """Difference in means in pooled-standard-deviation units.

    The usual randomisation check for a pre-treatment covariate: |SMD| below
    0.1 is conventionally read as balanced.
    """
    t, c = np.asarray(treatment, float), np.asarray(control, float)
    pooled = math.sqrt((t.var(ddof=1) + c.var(ddof=1)) / 2)
    return float((t.mean() - c.mean()) / pooled) if pooled else 0.0


def compare_proportions(
    treated_successes: int,
    treated_n: int,
    control_successes: int,
    control_n: int,
    alpha: float = 0.05,
) -> Comparison:
    """Difference in proportions with a Wald confidence interval and a pooled z-test."""
    p_t, p_c = treated_successes / treated_n, control_successes / control_n
    diff = p_t - p_c
    z_crit = stats.norm.ppf(1 - alpha / 2)
    se = math.sqrt(p_t * (1 - p_t) / treated_n + p_c * (1 - p_c) / control_n)
    pooled = (treated_successes + control_successes) / (treated_n + control_n)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / treated_n + 1 / control_n))
    z = diff / se_pooled if se_pooled else 0.0
    return Comparison(
        control_mean=p_c,
        treatment_mean=p_t,
        difference=diff,
        ci_low=diff - z_crit * se,
        ci_high=diff + z_crit * se,
        relative_lift=diff / p_c if p_c else math.nan,
        p_value=float(2 * stats.norm.sf(abs(z))),
    )


def compare_means(
    treated: np.ndarray,
    control: np.ndarray,
    alpha: float = 0.05,
    n_boot: int = 2000,
    seed: int = 7,
) -> Comparison:
    """Difference in means: Welch t-test p-value, bootstrap percentile CI.

    Spend is mostly zeros with a long right tail, so the interval is
    bootstrapped rather than assumed normal.
    """
    t, c = np.asarray(treated, float), np.asarray(control, float)
    diff = t.mean() - c.mean()
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = rng.choice(t, len(t)).mean() - rng.choice(c, len(c)).mean()
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return Comparison(
        control_mean=float(c.mean()),
        treatment_mean=float(t.mean()),
        difference=float(diff),
        ci_low=float(lo),
        ci_high=float(hi),
        relative_lift=float(diff / c.mean()) if c.mean() else math.nan,
        p_value=float(stats.ttest_ind(t, c, equal_var=False).pvalue),
    )


def holm(p_values: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, returned in the input order.

    Controls the chance of any false positive across several comparisons, and
    is uniformly more powerful than plain Bonferroni.
    """
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def sample_size_two_proportions(
    p_control: float, p_treatment: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Customers needed per arm to detect p_control -> p_treatment (two-sided)."""
    if p_control == p_treatment:
        raise ValueError("the two rates must differ")
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    p_bar = (p_control + p_treatment) / 2
    numerator = (
        z_a * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_b * math.sqrt(p_control * (1 - p_control) + p_treatment * (1 - p_treatment))
    ) ** 2
    return math.ceil(numerator / (p_control - p_treatment) ** 2)


def minimum_detectable_lift(
    p_control: float, n_per_arm: int, alpha: float = 0.05, power: float = 0.8
) -> float:
    """Smallest absolute increase over p_control detectable with n per arm.

    Solved numerically from sample_size_two_proportions, so the two functions
    are guaranteed to agree.
    """
    lo, hi = 1e-9, 1 - p_control - 1e-9
    if sample_size_two_proportions(p_control, p_control + hi, alpha, power) > n_per_arm:
        return math.nan
    for _ in range(100):
        mid = (lo + hi) / 2
        if sample_size_two_proportions(p_control, p_control + mid, alpha, power) > n_per_arm:
            lo = mid
        else:
            hi = mid
    return hi

"""Statistics tests. Expected values are worked out by hand in the comments."""

from __future__ import annotations

import math

import numpy as np
import pytest

from abtest import stats as st


def test_proportions_by_hand():
    # 200/1000 treated vs 150/1000 control.
    # Wald SE = sqrt(.2*.8/1000 + .15*.85/1000) = sqrt(.0002875) = .016956
    # CI = .05 +/- 1.95996 * .016956 = (.016767, .083233)
    # pooled p = .175, SE0 = sqrt(.175*.825*2/1000) = .016993, z = 2.9424
    c = st.compare_proportions(200, 1000, 150, 1000)
    assert c.difference == pytest.approx(0.05)
    assert c.ci_low == pytest.approx(0.016767, abs=1e-5)
    assert c.ci_high == pytest.approx(0.083233, abs=1e-5)
    assert c.relative_lift == pytest.approx(0.05 / 0.15)
    assert c.p_value == pytest.approx(0.003257, abs=2e-5)


def test_no_difference_gives_p_value_one():
    c = st.compare_proportions(100, 1000, 100, 1000)
    assert c.difference == 0
    assert c.p_value == pytest.approx(1.0)


def test_sample_size_matches_the_textbook_value():
    # 10% -> 12% at alpha .05, power .8: the classic answer is 3,841 per arm.
    assert st.sample_size_two_proportions(0.10, 0.12) == 3841


def test_more_power_or_smaller_effect_needs_more_customers():
    base = st.sample_size_two_proportions(0.10, 0.12)
    assert st.sample_size_two_proportions(0.10, 0.12, power=0.9) > base
    assert st.sample_size_two_proportions(0.10, 0.11) > base


def test_mde_inverts_sample_size():
    lift = st.minimum_detectable_lift(0.10, 3841)
    assert lift == pytest.approx(0.02, abs=1e-4)
    # With the MDE, the required n is at most the n we have.
    assert st.sample_size_two_proportions(0.10, 0.10 + lift) <= 3841


def test_equal_rates_rejected():
    with pytest.raises(ValueError):
        st.sample_size_two_proportions(0.1, 0.1)


def test_sample_ratio_mismatch():
    assert st.sample_ratio_mismatch([100, 100, 100], [1 / 3] * 3) == pytest.approx(1.0)
    # (150-100)^2/100 + 0 + (50-100)^2/100 = 50 on 2 df -> p = exp(-25)
    assert st.sample_ratio_mismatch([150, 100, 50], [1 / 3] * 3) == pytest.approx(
        math.exp(-25), rel=1e-6
    )
    with pytest.raises(ValueError):
        st.sample_ratio_mismatch([1, 2], [0.5, 0.6])


def test_holm_by_hand():
    # sorted: .01, .03, .04 -> 3*.01=.03, 2*.03=.06, max(.06, 1*.04)=.06
    assert st.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert st.holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])


def test_standardised_mean_difference():
    assert st.standardised_mean_difference([1, 2, 3], [1, 2, 3]) == 0
    # means 3 and 2, both sample variances 1 -> SMD = 1
    assert st.standardised_mean_difference([2, 3, 4], [1, 2, 3]) == pytest.approx(1.0)


def test_compare_means_bootstrap_brackets_the_difference():
    rng = np.random.default_rng(0)
    treated = rng.exponential(2.0, 3000)
    control = rng.exponential(1.0, 3000)
    c = st.compare_means(treated, control, n_boot=500)
    assert c.difference == pytest.approx(treated.mean() - control.mean())
    assert c.ci_low < c.difference < c.ci_high
    assert c.ci_low > 0
    assert c.p_value < 1e-10

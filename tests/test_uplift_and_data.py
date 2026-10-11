from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from abtest import data as d
from abtest import uplift as u


def test_qini_by_hand():
    # Customers sorted by score: T1 (y=1), C0 (y=0), T0 (y=0), C1 (y=1)
    scores = np.array([4, 3, 2, 1])
    treated = np.array([1, 0, 1, 0])
    y = np.array([1, 0, 0, 1])
    share, gain = u.qini_curve(scores, treated, y)
    # k=1: no control yet -> 0. k=2: 1 - 0*1/1 = 1. k=3: 1 - 0*2/1 = 1.
    # k=4: 1 - 1*2/2 = 0.
    assert share.tolist() == [0, 0.25, 0.5, 0.75, 1.0]
    assert gain.tolist() == pytest.approx([0, 0, 1, 1, 0])


def test_oracle_beats_random_and_random_is_near_zero():
    df = d.synthetic(40_000, seed=1)
    treated = (df["segment"] == "Womens E-Mail").to_numpy()
    keep = treated | (df["segment"] == "No E-Mail").to_numpy()
    y, t = df["conversion"].to_numpy()[keep], treated[keep]
    oracle = df["womens"].to_numpy()[keep]  # the true uplift is only for womens == 1
    rng = np.random.default_rng(3)
    assert u.qini_coefficient(oracle, t, y) > 0.2
    assert abs(u.qini_coefficient(rng.random(len(y)), t, y)) < 0.2


def test_t_learner_finds_the_planted_segment():
    df = d.synthetic(60_000, seed=2)
    arm = df[df["segment"].isin(["Womens E-Mail", "No E-Mail"])]
    X, names = d.model_matrix(arm)
    t = (arm["segment"] == "Womens E-Mail").to_numpy()
    model = u.TLearner(LogisticRegression(max_iter=1000)).fit(X, t, arm["conversion"].to_numpy())
    uplift = model.predict_uplift(X)
    womens = arm["womens"].to_numpy() == 1
    assert uplift[womens].mean() > uplift[~womens].mean()


def test_targeting_value_on_the_planted_effect():
    df = d.synthetic(60_000, seed=4)
    arm = df[df["segment"].isin(["Womens E-Mail", "No E-Mail"])]
    t = (arm["segment"] == "Womens E-Mail").to_numpy()
    v = u.targeting_value(arm["womens"].to_numpy(), t, arm["conversion"].to_numpy(), share=0.5)
    # Targeting the half that can respond roughly doubles the per-customer effect.
    assert v["uplift_in_targeted"] > v["uplift_overall"] > 0
    assert v["ratio_to_average"] > 1.5
    with pytest.raises(ValueError):
        u.targeting_value(np.zeros(3), np.array([1, 0, 1]), np.zeros(3), share=0)


def test_load_rejects_a_broken_file(tmp_path):
    df = d.synthetic(500)
    good = tmp_path / "good.csv"
    df.to_csv(good, index=False)
    assert len(d.load(good)) == 500

    bad = df.copy()
    bad.loc[0, "segment"] = "SMS"
    path = tmp_path / "bad.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError, match="arms"):
        d.load(path)

    with pytest.raises(ValueError, match="missing columns"):
        df.drop(columns=["spend"]).to_csv(path, index=False)
        d.load(path)


def test_model_matrix_one_hot_drops_the_reference_level():
    df = d.synthetic(200)
    X, names = d.model_matrix(df)
    assert X.shape == (200, len(names))
    assert "zip_code=Surburban" not in names  # reference level
    assert {"zip_code=Urban", "zip_code=Rural", "channel=Web", "channel=Multichannel"} <= set(names)
    assert isinstance(df, pd.DataFrame)

"""Uplift modelling: which customers does the campaign actually change?

An A/B test answers "does the email work on average?". Uplift modelling asks
"for whom?", so the next campaign can go only to customers it persuades. That
is only answerable because the experiment was randomised: within any group of
similar customers, the treated and untreated are comparable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.base import ClassifierMixin, clone


@dataclass
class TLearner:
    """Two models: P(outcome | treated, x) and P(outcome | control, x).

    Predicted uplift is the difference. Simple and transparent; its weakness is
    that each model is trained on only part of the data.
    """

    base: ClassifierMixin

    def fit(self, X: np.ndarray, treated: np.ndarray, y: np.ndarray) -> TLearner:
        treated = np.asarray(treated, bool)
        self.treated_model_ = clone(self.base).fit(X[treated], y[treated])
        self.control_model_ = clone(self.base).fit(X[~treated], y[~treated])
        return self

    def predict_uplift(self, X: np.ndarray) -> np.ndarray:
        return (
            self.treated_model_.predict_proba(X)[:, 1] - self.control_model_.predict_proba(X)[:, 1]
        )


def qini_curve(
    scores: np.ndarray, treated: np.ndarray, y: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Incremental outcomes from targeting the top-scored customers first.

    At each cut-off k (customers sorted by predicted uplift, highest first):

        gain(k) = Y_treated(k) - Y_control(k) * N_treated(k) / N_control(k)

    i.e. treated outcomes minus what the same number of treated customers
    would have produced at the control rate. Returns (share targeted, gain).
    """
    scores, treated, y = np.asarray(scores), np.asarray(treated, bool), np.asarray(y, float)
    order = np.argsort(-scores, kind="stable")
    t, yy = treated[order], y[order]
    n_t = np.cumsum(t)
    n_c = np.cumsum(~t)
    y_t = np.cumsum(yy * t)
    y_c = np.cumsum(yy * ~t)
    with np.errstate(divide="ignore", invalid="ignore"):
        gain = np.where(n_c > 0, y_t - y_c * n_t / n_c, 0.0)
    share = np.arange(1, len(scores) + 1) / len(scores)
    return np.concatenate([[0.0], share]), np.concatenate([[0.0], gain])


def qini_coefficient(scores: np.ndarray, treated: np.ndarray, y: np.ndarray) -> float:
    """Area between the model's Qini curve and random targeting, scaled by the total gain.

    0 means no better than random; positive means the model ranks persuadable
    customers first. Normalised so different-sized samples are comparable.
    """
    share, gain = qini_curve(scores, treated, y)
    random_line = share * gain[-1]
    area = np.trapezoid(gain - random_line, share)
    return float(area / abs(gain[-1])) if gain[-1] else float("nan")


def targeting_value(
    scores: np.ndarray, treated: np.ndarray, y: np.ndarray, share: float
) -> dict[str, float]:
    """Estimated effect of sending the campaign to the top `share` by predicted uplift.

    Within the targeted group the effect is measured directly (treated rate
    minus control rate), which is valid because assignment was random.
    """
    if not 0 < share <= 1:
        raise ValueError("share must be in (0, 1]")
    scores, treated, y = np.asarray(scores), np.asarray(treated, bool), np.asarray(y, float)
    k = int(np.ceil(share * len(scores)))
    top = np.argsort(-scores, kind="stable")[:k]
    t, yy = treated[top], y[top]
    rate_t = yy[t].mean() if t.any() else float("nan")
    rate_c = yy[~t].mean() if (~t).any() else float("nan")
    overall = y[treated].mean() - y[~treated].mean()
    return {
        "share_targeted": share,
        "uplift_in_targeted": float(rate_t - rate_c),
        "uplift_overall": float(overall),
        "ratio_to_average": float((rate_t - rate_c) / overall) if overall else float("nan"),
    }

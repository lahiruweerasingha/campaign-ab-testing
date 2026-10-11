# 3. Uplift judged on customers the models never saw

**Status:** accepted

## Context

The average effect says whether to send the e-mail to everyone. The more
useful question is whom to send it to. A customer's uplift (outcome if sent
minus outcome if not) is never observed for that customer, so an uplift model
cannot be scored row by row the way a classifier can.

## Decision

- **T-learners**: one model of conversion for treated customers and one for
  control; predicted uplift is the difference. Two base models, logistic
  regression and gradient boosting, so a simple and a flexible model are
  compared on the same footing.
- Features are **pre-treatment only** (recency, past spend, past purchase
  categories, new customer, area, channel).
- Models are trained on a random half of each e-mail-vs-control sample,
  stratified by arm and outcome, and evaluated on the other half.
- Evaluation uses what randomisation makes measurable: the **Qini curve**
  (incremental conversions when targeting the highest predicted uplift first),
  its coefficient relative to random targeting, and the **measured** effect
  (treated rate minus control rate) among the top 10%, 30% and 50%.
- A **permutation test** of the Qini coefficient: the share of 1,000 random
  rankings of the same held-out customers that score at least as high. Added
  after the first real-data run, where a Qini of 0.18 looked convincing on
  its own but rested on about 34 incremental conversions.

## Result

On the Hillstrom data the men's e-mail models do no better than random
(Qini p 0.899 and 0.664). The women's e-mail models reach Qini p 0.053
(logistic) and 0.042 (gradient boosting), and disagree about the top 10%
(0.97% vs 0.34% uplift). On synthetic data of the same size with a real
segment, the same models reach p 0.008 and 0.005. The conclusion reported is
that this experiment cannot say reliably whom to target.

## Consequences

- The T-learner is a baseline: each model sees only part of the data, which
  makes the uplift estimate noisy. X-learners or causal forests are the next
  comparison.
- The Qini coefficient is normalised by the total incremental gain, so it is
  undefined when the e-mail has no overall effect; the targeting table is
  still reported.

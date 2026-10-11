# 4. Prove the pipeline on planted effects before trusting it on real data

**Status:** accepted

## Context

On real data the true effects are unknown, so a wrong formula, a swapped arm
label or a leak between training and evaluation halves can produce plausible
numbers that nobody can check.

## Decision

`abtest.data.synthetic` generates an experiment with the real data's columns
and known effects: a uniform +0.4-point conversion lift from the men's e-mail,
and a +1.2-point lift from the women's e-mail **only** for customers with past
women's purchases. `make synthetic-check` runs the full pipeline on it, and CI
runs the same pipeline on every push.

## Result

From `evidence/synthetic_check/RESULTS.md`: the randomisation checks pass
(sample-ratio p = 0.611, largest |SMD| 0.010); the men's lift is estimated at
+0.44 points (CI 0.27 to 0.62) and the women's average lift at +0.51 points
(CI 0.33 to 0.69) against about +0.6 planted; uplift models find no segment
for the men's e-mail (Qini −0.066 and 0.019) and find the planted one for the
women's e-mail (Qini 0.171 and 0.182, 1.12–1.44 points among the top 10%).

## Consequences

- Synthetic results live only in `evidence/synthetic_check/`, and every file
  there is labelled as synthetic, so they cannot be mistaken for real results.
- The planted effects are deliberately clean. Recovering them is necessary
  but not sufficient evidence that the method works on real data.

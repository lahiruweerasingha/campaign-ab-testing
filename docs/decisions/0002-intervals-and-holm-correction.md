# 2. Intervals and a multiple-testing correction, not single p-values

**Status:** accepted

## Context

Two e-mails and three outcomes make six comparisons against control. At a 5%
level each, six independent tests would produce at least one false positive
26% of the time even if neither e-mail did anything. And a p-value alone says
nothing about how large an effect is, which is what a campaign decision needs.

## Decision

- Every effect is reported as a **difference with a 95% confidence interval**
  and a relative lift.
- Visit and conversion: difference in proportions, Wald interval, pooled
  two-proportion z-test.
- Spend: difference in means with a **bootstrap** percentile interval (spend is
  mostly zeros with a long right tail, so a normal interval is doubtful) and a
  Welch t-test p-value.
- **Holm-Bonferroni** adjustment across all six p-values. It controls the
  chance of any false positive like Bonferroni, and is never less powerful.
- A **minimum detectable lift** for conversion, so a non-significant result
  can be read as "too small to detect with this sample" rather than "no effect".

## Consequences

- Every formula is plain NumPy/SciPy and checked in `tests/test_stats.py`
  against values worked out by hand (including the textbook 3,841 customers
  per arm for detecting 10% -> 12%).
- Wald intervals are adequate at tens of thousands per arm; small arms would
  need Wilson or Newcombe intervals.

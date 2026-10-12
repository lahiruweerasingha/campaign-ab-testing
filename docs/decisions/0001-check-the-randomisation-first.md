# 1. Check the randomisation before reading any effect

**Status:** accepted

## Context

An experiment's effect estimates are only causal if assignment worked as
designed. Common failures (a logging bug that drops some treated customers, a
filter applied to one arm, a broken randomiser) do not announce themselves;
they show up as arms of the wrong size or arms that differ before treatment.

## Decision

Before any effect is computed, `run_analysis.py` reports:

- a **sample-ratio mismatch** test: a chi-square test of the arm sizes against
  the intended 1/3 split;
- the **standardised mean difference** of each numeric pre-treatment covariate
  (recency, past spend, past men's and women's purchases, new customer)
  between each e-mail arm and control, with |SMD| < 0.1 read as balanced.

Both are written to `results.json` and shown first in `RESULTS.md`.

## Consequences

- A tiny sample-ratio p-value is treated as a stop sign, not a footnote.
- Only pre-treatment covariates are checked. Outcomes are never used to judge
  balance, and channel and area are left to the uplift models.

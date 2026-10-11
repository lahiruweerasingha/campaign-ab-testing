# Results

Data: data/hillstrom.csv. Customers: 64,000.

## 1. Is the experiment sound?

| Arm | Customers |
|---|---:|
| No E-Mail | 21,306 |
| Mens E-Mail | 21,307 |
| Womens E-Mail | 21,387 |

- Sample-ratio mismatch test (intended 1/3 each): p = 0.904
- Largest covariate imbalance: |SMD| = 0.009 (balanced; threshold 0.1)

## 2. What did each e-mail do? (vs no e-mail)

| E-mail | Outcome | No e-mail | E-mail | Difference (95% CI) | Relative lift | p (Holm) |
|---|---|---:|---:|---|---:|---:|
| Mens E-Mail | visit | 10.62% | 18.28% | 7.66% (7.00% to 8.32%) | +72% | 3.4e-111 |
| Mens E-Mail | conversion | 0.57% | 1.25% | 0.68% (0.50% to 0.86%) | +119% | 6.1e-13 |
| Mens E-Mail | spend | 0.65 | 1.42 | 0.77 (0.49 to 1.03) | +118% | 3.5e-07 |
| Womens E-Mail | visit | 10.62% | 15.14% | 4.52% (3.89% to 5.16%) | +43% | 1.6e-43 |
| Womens E-Mail | conversion | 0.57% | 0.88% | 0.31% (0.15% to 0.47%) | +54% | 0.00031 |
| Womens E-Mail | spend | 0.65 | 1.08 | 0.42 (0.17 to 0.68) | +65% | 0.0011 |

## 3. Was it big enough?

With 21,306 customers per arm and a 0.57% control conversion rate, the smallest conversion lift detectable with 80% power at 5% significance is 0.224% absolute (39% relative).

## 4. For whom? Uplift on the held-out half

Qini p: the share of 1,000 random rankings of the same held-out customers
that reach at least the model's Qini coefficient. A large p means the curve
is above the random line by no more than chance would put it there.

| E-mail | Model | Qini coefficient | Qini p | Uplift if top 10% targeted | top 30% | top 50% | Average uplift |
|---|---|---:|---:|---:|---:|---:|---:|
| Mens E-Mail | logistic T-learner | -0.073 | 0.899 | 0.57% | 0.61% | 0.48% | 0.69% |
| Mens E-Mail | gradient boosting T-learner | -0.024 | 0.664 | 0.15% | 0.70% | 0.59% | 0.69% |
| Womens E-Mail | logistic T-learner | 0.168 | 0.053 | 0.97% | 0.51% | 0.49% | 0.32% |
| Womens E-Mail | gradient boosting T-learner | 0.176 | 0.042 | 0.34% | 0.56% | 0.37% | 0.32% |

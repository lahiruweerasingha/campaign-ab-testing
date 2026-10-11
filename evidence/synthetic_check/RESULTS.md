# Results

Data: synthetic (pipeline check). Customers: 64,000.

## 1. Is the experiment sound?

| Arm | Customers |
|---|---:|
| No E-Mail | 21,305 |
| Mens E-Mail | 21,248 |
| Womens E-Mail | 21,447 |

- Sample-ratio mismatch test (intended 1/3 each): p = 0.611
- Largest covariate imbalance: |SMD| = 0.010 (balanced; threshold 0.1)

## 2. What did each e-mail do? (vs no e-mail)

| E-mail | Outcome | No e-mail | E-mail | Difference (95% CI) | Relative lift | p (Holm) |
|---|---|---:|---:|---|---:|---:|
| Mens E-Mail | visit | 10.46% | 13.16% | 2.70% (2.09% to 3.31%) | +26% | 3e-17 |
| Mens E-Mail | conversion | 0.64% | 1.09% | 0.44% (0.27% to 0.62%) | +69% | 2.3e-06 |
| Mens E-Mail | spend | 0.84 | 1.20 | 0.35 (0.11 to 0.61) | +42% | 0.0064 |
| Womens E-Mail | visit | 10.46% | 14.29% | 3.83% (3.21% to 4.45%) | +37% | 1.7e-32 |
| Womens E-Mail | conversion | 0.64% | 1.16% | 0.51% (0.33% to 0.69%) | +80% | 7.8e-08 |
| Womens E-Mail | spend | 0.84 | 1.46 | 0.61 (0.33 to 0.88) | +73% | 4.4e-05 |

## 3. Was it big enough?

With 21,248 customers per arm and a 0.64% control conversion rate, the smallest conversion lift detectable with 80% power at 5% significance is 0.236% absolute (37% relative).

## 4. For whom? Uplift on the held-out half

| E-mail | Model | Qini coefficient | Uplift if top 10% targeted | top 30% | top 50% | Average uplift |
|---|---|---:|---:|---:|---:|---:|
| Mens E-Mail | logistic T-learner | -0.066 | 0.30% | 0.48% | 0.47% | 0.45% |
| Mens E-Mail | gradient boosting T-learner | 0.019 | 0.40% | 0.40% | 0.39% | 0.45% |
| Womens E-Mail | logistic T-learner | 0.171 | 1.12% | 0.77% | 0.86% | 0.52% |
| Womens E-Mail | gradient boosting T-learner | 0.182 | 1.44% | 0.75% | 0.74% | 0.52% |

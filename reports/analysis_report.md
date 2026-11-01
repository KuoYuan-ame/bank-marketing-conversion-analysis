# Historical Marketing Conversion — Analysis Report

## Objective and measurement

Study historical term-deposit subscription outcomes using record-level conversion rates and group-level summaries. This is a descriptive analysis of an existing campaign dataset, not an estimate of causal marketing lift. The core KPI is `SUM(y='yes') / COUNT(*)` per marketing observation.

## Data integrity

The analysis includes 45,211 observations and 5,289 subscriptions (11.70%). Source `unknown` categories are not treated as ordinary SQL `NULL`; `pdays=-1` is a source-specific code for no previous contact. A synthetic `record_id` identifies *rows*, not people. The lack of a customer ID limits customer-level interpretation.

## Campaign frequency and segmentation

| Contact-frequency band | Records | Subscriptions | Observed rate |
|---|---:|---:|---:|
| 1 | 17,544 | 2,561 | 14.60% |
| 2 | 12,505 | 1,401 | 11.20% |
| 3–4 | 9,043 | 935 | 10.34% |
| 5+ | 6,119 | 392 | 6.41% |

Contact-frequency groups display declining historical subscription rates, but final contact count is itself a post-process outcome; the direction does not establish effects of additional contact. This association also appears separately within housing-loan groups.

## Prior outcomes and candidate segments

- `poutcome=success`: 978/1,511 = 64.73%; `poutcome=unknown`: 9.16% among 36,959 observations.
- Among screened segments (at least 200 records), the student/no-housing-loan/no-personal-loan group has the highest observed rate: 247/681 = 36.27%, descriptive Lift 3.10×.
- Management/no-housing-loan/no-personal-loan has the largest historical subscription count within the screened groups: 829/4,233 = 19.58%.
- The ten-segment shortlist contains 16,473 observations and 3,042 subscriptions; selection on in-sample outcomes risks optimistic assessment.

## Uncertainty assessment

Wilson 95% intervals are computed for each shortlisted proportion. The student/no-loan group's interval is [32.75%, 39.95%], while the management/no-loan group's interval is approximately [18.42%, 20.81%]. `self-employed` ranks ahead of `technician` on point estimates, whereas their ranks reverse if sorted by Wilson lower bounds. This illustrates the impact of group sample size on precision. Since groups were chosen after exploring the same data, these are exploratory uncertainty summaries, not confirmatory subgroup claims.

## Proposed validation, not measured effects

Before adopting any targeting policy, obtain compliant customer IDs and define the eligible customer population. Freeze a policy before testing; randomize eligible customers into policy and control arms. Use intention-to-treat subscription per eligible customer as the primary outcome and prespecify follow-up duration, sample size, MDE, significance level, and monitoring. Track opt-outs, complaints, suitability, customer experience and contact volume as guardrails. Add costs and product margin to estimate incremental business value. None of these outcomes can be recovered from this historical dataset alone.

## Limitations

No unique customer ID, costs, randomized policy-control comparison or reliable full event timeline; final `campaign` and `duration` may constitute post-contact leakage. Group-level differences do not imply a causal effect or an objective justification for unequal access to financial products.

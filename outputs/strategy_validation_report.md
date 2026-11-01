# Bank Marketing: Segment Stability and Strategy Validation

## 1. Data scope

- Source: UCI Bank Marketing, legacy `bank-full.csv`.
- Full historical dataset: 45,211 marketing records, 5,289 subscriptions; observed rate 11.70%.
- Current input: 10 shortlisted segment rows totaling 16,473 historical records (36.44% of all records) and 3,042 subscriptions (57.52% of all subscriptions).
- These are observation-level summaries, not deduplicated customers. Segments are selected using the same history being summarized.

## 2. Descriptive findings

- Highest observed rate among the **provided shortlist**: `student / housing=no / loan=no`, 36.27% (247/681), 95% Wilson interval [32.75%, 39.95%].
- Largest absolute subscription count among the shortlist: `management / housing=no / loan=no`, 829 successes from 4,233 records; observed rate 19.58%.
- Top four **by in-sample observed rate**: 7,193 records (15.91% of the dataset), 1,688 subscriptions (31.92% of all observed subscriptions).
- `historical_lift` means segment observed rate divided by overall historical rate; it is **not** incremental uplift.

## 3. Statistical stability

- `segment_uncertainty.csv` includes the observed rate, Wilson 95% interval, and rank by point estimate / interval lower bound.
- Wilson intervals provide an indication of sampling uncertainty **under an independent Bernoulli approximation**. They do not correct for selection, multiple comparisons, repeated contacts from the same customer, or possible confounding.
- The shortlist originates from historical rates; ranking by these same data tends to overstate the expected advantage of the top-ranked segments.
- The prior SQL minimum 200 records and plot minimum 500 records are filtering choices, **not guarantees** of statistical reliability.

## 4. Proposed operational validation (not measured in this dataset)

1. Define the eligible customer population and obtain a persistent customer-level ID. Apply consent, suitability, compliance, and fair-treatment checks before outreach.
2. Freeze the segment-selection policy before testing. Randomly assign eligible customers to policy vs existing outreach strategy; use intention-to-treat analysis.
3. Primary outcome: subscriptions per eligible customer within a prespecified window. Guardrails: contacts per customer, opt-outs, complaints, customer experience and compliance.
4. Prespecify experiment duration, alpha, power/MDE, tracking quality checks, and stopping rules. Add cost per contact / product margin to evaluate net business value.
5. Compare **incremental** performance between randomized arms, not subgroup historical rates alone.

## 5. Interpretation limitations

- This historical dataset has no unique customer ID, per-contact cost, product margin, or randomized policy-control comparison.
- `duration` and final `campaign` are not suitable pre-contact targeting features; `poutcome` may be used only if known at the relevant decision time.
- No claims are made about causal effects, future conversion probabilities, revenue lift, campaign savings, or suitability of any occupation group.

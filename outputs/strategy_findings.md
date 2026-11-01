# Bank Marketing: Customer Segmentation Findings

## Data and scope
- Source: UCI Bank Marketing (legacy bank-full.csv), record-level results.
- Total historical records: 45,211; subscriptions: 5,289; observed rate: 11.70%.
- Q6 and Q7 reconcile to full dataset. Q8 retains 35 segments with at least 200 observations, covering 44,433 records (98.28%) and 5,236 subscriptions (99.00%). Excluded smaller groups: 778 records.

## Previous campaign outcome (Q6)
- `success`: 1,511 records, 978 subscriptions, 64.73% observed rate.
- `unknown`: 36,959 records (81.75% of all observations), 9.16% observed rate. `unknown` must not automatically be equated with never contacted.
- These rates are associations; they do not measure the increment caused by contacting again.

## Housing loan and previous outcome (Q7)
- `housing=no` and `poutcome=success`: 70.10% (n=1,040).
- `housing=yes` and `poutcome=success`: 52.87% (n=471).
- Group totals: housing=no 20,081 records and 3,354 subscriptions; housing=yes 25,130 records and 1,935 subscriptions.

## Pre-contact candidate segments (Q8)
- Highest observed rate in screened groups: **student | housing=no | loan=no**, 36.27% (247/681), lift 3.10x relative to total historical average.
- Largest number of observed subscriptions: **management | housing=no | loan=no**, 829 subscriptions from 4,233 records; historical rate 19.58%.
- Top four groups **by observed rate** account for 7,193 records (15.91%) and 1,688 subscriptions (31.92%); this is an in-sample description, not a forecast of future lift.
- Historical subscription rate alone is insufficient to select outreach targets. Consider segment size, costs, consent, channel capacity, uncertainty, and fair treatment.

## Important limitations
- Rows are marketing observations, not deduplicated customers. No unique customer ID is available.
- Historical data do not establish causal effects or incremental response to future calls; segment ranking is in-sample and may be optimistic.
- Thresholds of 200 (SQL) and 500 (visual shortlist) are presentation choices, not statistical guarantees.
- Prior-campaign outcomes are eligible pre-contact features only if actually available at the time of the intended decision.
- No per-contact cost, product margin, or control group is provided. No profit or causal uplift estimates are claimed.

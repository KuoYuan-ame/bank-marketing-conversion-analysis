-- Bank Marketing: Customer Segmentation for Pre-contact Prioritization
-- Source table: bank_marketing_project.bank_marketing
-- Unit: marketing observation, NOT unique customer.
-- Associations are descriptive, NOT causal effects.
-- Caution: campaign and duration are excluded because their final values may not be known before outreach.

-- QUERY: previous_outcome
-- Q6: Compare previous campaign results (including unknown).
SELECT
    poutcome,
    COUNT(*) AS records,
    SUM(y = 'yes') AS conversions,
    ROUND(100.0 * AVG(y = 'yes'), 2) AS conversion_rate_pct
FROM bank_marketing_project.bank_marketing
GROUP BY poutcome
ORDER BY conversion_rate_pct DESC;

-- QUERY: housing_previous_segments
-- Q7: Within each housing-loan group, examine prior-campaign outcome.
WITH group_stats AS (
    SELECT
        housing,
        poutcome,
        COUNT(*) AS records,
        SUM(y = 'yes') AS conversions,
        AVG(y = 'yes') AS rate_decimal
    FROM bank_marketing_project.bank_marketing
    GROUP BY housing, poutcome
)
SELECT
    housing,
    poutcome,
    records,
    conversions,
    ROUND(100.0 * rate_decimal, 2) AS conversion_rate_pct,
    DENSE_RANK() OVER (
        PARTITION BY housing ORDER BY rate_decimal DESC
    ) AS rate_rank_within_housing,
    ROUND(
        100.0 * conversions / NULLIF(
            SUM(conversions) OVER (PARTITION BY housing), 0
        ), 2
    ) AS conversion_share_within_housing_pct
FROM group_stats
ORDER BY housing, rate_rank_within_housing;

-- QUERY: candidate_segments
-- Q8: Practical candidate segments using pre-contact attributes only.
-- 200-record threshold prevents very small segments from topping a naive rate ranking.
-- This filter intentionally EXCLUDES small groups; totals won't match the full dataset.
WITH segments AS (
    SELECT
        job,
        housing,
        loan,
        COUNT(*) AS records,
        SUM(y = 'yes') AS conversions,
        AVG(y = 'yes') AS rate_decimal
    FROM bank_marketing_project.bank_marketing
    GROUP BY job, housing, loan
    HAVING COUNT(*) >= 200
),
baseline AS (
    SELECT AVG(y = 'yes') AS overall_rate
    FROM bank_marketing_project.bank_marketing
)
SELECT
    s.job,
    s.housing,
    s.loan,
    s.records,
    s.conversions,
    ROUND(100.0 * s.rate_decimal, 2) AS conversion_rate_pct,
    ROUND(s.rate_decimal / NULLIF(b.overall_rate, 0), 2) AS lift_vs_overall,
    DENSE_RANK() OVER (ORDER BY s.rate_decimal DESC) AS rank_by_rate,
    DENSE_RANK() OVER (ORDER BY s.conversions DESC) AS rank_by_volume
FROM segments AS s
CROSS JOIN baseline AS b
ORDER BY rank_by_rate, s.records DESC;

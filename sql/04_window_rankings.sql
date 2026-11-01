-- Bank Marketing: housing-loan x campaign-contact bands with window functions.
-- Descriptive SQL only; observations are not necessarily unique customers.
USE bank_marketing_project;

-- Q5: Within each housing segment, rank contact-frequency bands by subscription rate.
WITH assigned AS (
    SELECT
        housing,
        CASE
            WHEN campaign = 1 THEN '1_contact'
            WHEN campaign = 2 THEN '2_contacts'
            WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
            ELSE '5_plus_contacts'
        END AS contact_band,
        CASE
            WHEN campaign = 1 THEN 1
            WHEN campaign = 2 THEN 2
            WHEN campaign BETWEEN 3 AND 4 THEN 3
            ELSE 4
        END AS band_order,
        y
    FROM bank_marketing
), segment_stats AS (
    SELECT
        housing,
        contact_band,
        band_order,
        COUNT(*) AS records,
        SUM(y = 'yes') AS conversions,
        AVG(y = 'yes') AS rate_decimal
    FROM assigned
    GROUP BY housing, contact_band, band_order
)
SELECT
    housing,
    contact_band,
    records,
    conversions,
    ROUND(100 * rate_decimal, 2) AS conversion_rate_pct,
    DENSE_RANK() OVER (
        PARTITION BY housing
        ORDER BY rate_decimal DESC
    ) AS rate_rank_within_housing,
    ROUND(100.0 * conversions / SUM(conversions) OVER (PARTITION BY housing), 2)
        AS conversion_share_within_housing_pct,
    ROUND(100.0 * records / SUM(records) OVER (PARTITION BY housing), 2)
        AS record_share_within_housing_pct
FROM segment_stats
ORDER BY housing, rate_rank_within_housing, band_order;

-- Q6: Rank all eight segments by their total number of subscriptions.
WITH assigned AS (
    SELECT
        housing,
        CASE
            WHEN campaign = 1 THEN '1_contact'
            WHEN campaign = 2 THEN '2_contacts'
            WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
            ELSE '5_plus_contacts'
        END AS contact_band,
        y
    FROM bank_marketing
), segment_stats AS (
    SELECT
        housing,
        contact_band,
        COUNT(*) AS records,
        SUM(y = 'yes') AS conversions,
        ROUND(100.0 * AVG(y = 'yes'), 2) AS conversion_rate_pct
    FROM assigned
    GROUP BY housing, contact_band
)
SELECT
    housing,
    contact_band,
    records,
    conversions,
    conversion_rate_pct,
    DENSE_RANK() OVER (ORDER BY conversions DESC) AS rank_by_conversion_count,
    ROUND(100.0 * conversions / SUM(conversions) OVER (), 2)
        AS share_of_all_subscriptions_pct
FROM segment_stats
ORDER BY rank_by_conversion_count, housing, contact_band;

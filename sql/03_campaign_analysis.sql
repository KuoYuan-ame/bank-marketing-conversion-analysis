-- Bank Marketing | Current-campaign contact frequency analysis
-- Source: UCI Bank Marketing, legacy bank-full.csv.
-- Unit of analysis: an observation/marketing record, NOT a distinct customer.
-- campaign = number of contacts made during the CURRENT campaign for the client,
-- including the last contact; y = whether the term deposit was subscribed.
-- Results are descriptive associations and do not identify the causal effect of calls.
-- Prerequisite: bank_marketing_project.bank_marketing already contains 45,211 rows.
-- MySQL 8.0+

USE bank_marketing_project;

-- Q1. Import check and contact-frequency range.
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2) AS overall_conversion_pct,
    MIN(campaign) AS min_contacts,
    MAX(campaign) AS max_contacts,
    ROUND(AVG(campaign), 2) AS avg_contacts
FROM bank_marketing;

-- Q2. Core analysis: four mutually exclusive contact-frequency bands.
-- Compute the overall benchmark separately, then compare each band with it.
WITH banded AS (
    SELECT
        y,
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
        END AS band_order
    FROM bank_marketing
),
overall_stats AS (
    SELECT COUNT(*) AS all_records,
           AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) AS overall_rate
    FROM bank_marketing
),
band_stats AS (
    SELECT
        contact_band,
        band_order,
        COUNT(*) AS records,
        SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
        AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) AS conversion_rate
    FROM banded
    GROUP BY contact_band, band_order
)
SELECT
    b.contact_band,
    b.records,
    b.conversions,
    ROUND(100.0 * b.conversion_rate, 2) AS conversion_rate_pct,
    ROUND(100.0 * b.records / o.all_records, 2) AS record_share_pct,
    ROUND(100.0 * (b.conversion_rate - o.overall_rate), 2) AS vs_overall_pp
FROM band_stats AS b
CROSS JOIN overall_stats AS o
ORDER BY b.band_order;

-- Q3. Drill down: exact contact counts 1 to 10, group the long tail as 11+.
WITH detailed AS (
    SELECT
        y,
        CASE WHEN campaign <= 10 THEN CAST(campaign AS CHAR) ELSE '11_plus' END AS contact_count,
        CASE WHEN campaign <= 10 THEN campaign ELSE 11 END AS sort_order
    FROM bank_marketing
)
SELECT
    contact_count,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2) AS conversion_rate_pct
FROM detailed
GROUP BY contact_count, sort_order
ORDER BY sort_order;

-- Q4. Two-dimensional analysis: housing loan x current-campaign contacts.
WITH banded AS (
    SELECT
        housing,
        y,
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
        END AS band_order
    FROM bank_marketing
)
SELECT
    housing,
    contact_band,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2) AS conversion_rate_pct
FROM banded
GROUP BY housing, contact_band, band_order
ORDER BY housing, band_order;

-- Q5. Window function: rank contact bands WITHIN each housing group.
-- Keep the precise rate for ranking; round only for display.
WITH banded AS (
    SELECT
        housing,
        y,
        CASE
            WHEN campaign = 1 THEN '1_contact'
            WHEN campaign = 2 THEN '2_contacts'
            WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
            ELSE '5_plus_contacts'
        END AS contact_band
    FROM bank_marketing
),
group_stats AS (
    SELECT
        housing,
        contact_band,
        COUNT(*) AS records,
        SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
        AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) AS conversion_rate
    FROM banded
    GROUP BY housing, contact_band
)
SELECT
    housing,
    contact_band,
    records,
    conversions,
    ROUND(100.0 * conversion_rate, 2) AS conversion_rate_pct,
    DENSE_RANK() OVER (
        PARTITION BY housing
        ORDER BY conversion_rate DESC
    ) AS within_housing_rank
FROM group_stats
ORDER BY housing, within_housing_rank, contact_band;

-- Q6. Context check: previous-campaign outcome x contact band.
-- Watch sparse groups and do not compare rates as causal effects.
WITH banded AS (
    SELECT
        poutcome,
        y,
        CASE
            WHEN campaign = 1 THEN '1_contact'
            WHEN campaign = 2 THEN '2_contacts'
            WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
            ELSE '5_plus_contacts'
        END AS contact_band
    FROM bank_marketing
)
SELECT
    poutcome,
    contact_band,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2) AS conversion_rate_pct
FROM banded
GROUP BY poutcome, contact_band
ORDER BY poutcome, contact_band;

-- Q7. Job-group contribution versus rate: large and high-rate groups can differ.
WITH job_stats AS (
    SELECT
        job,
        COUNT(*) AS records,
        SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
        AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) AS conversion_rate
    FROM bank_marketing
    GROUP BY job
)
SELECT
    job,
    records,
    conversions,
    ROUND(100.0 * conversion_rate, 2) AS conversion_rate_pct,
    ROUND(100.0 * conversions / SUM(conversions) OVER (), 2) AS share_of_all_conversions_pct,
    DENSE_RANK() OVER (ORDER BY conversion_rate DESC) AS conversion_rate_rank
FROM job_stats
ORDER BY conversions DESC, job;

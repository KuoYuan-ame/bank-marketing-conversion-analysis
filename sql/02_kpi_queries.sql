-- Run these queries in MySQL Workbench AFTER importing bank_mysql_import.csv.
-- Each source row is one observation; no unique customer identifier exists.
USE bank_marketing_project;

-- Q1. Import validation: expected 45,211 records and 5,289 subscriptions.
SELECT
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(
        100.0 * SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct,
    MIN(record_id) AS min_record_id,
    MAX(record_id) AS max_record_id,
    COUNT(DISTINCT record_id) AS distinct_record_ids
FROM bank_marketing;

-- Q2. Segment-level subscription rates, in record counts (not distinct clients).
SELECT
    job,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY job
ORDER BY records DESC;

-- Q3. Housing loan: compare group sizes and conversion rates.
SELECT
    housing,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY housing
ORDER BY records DESC;

-- Q4. Personal loan comparison.
SELECT
    loan,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY loan
ORDER BY records DESC;

-- Q5. Previously observed campaign outcome.
SELECT
    poutcome,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY poutcome
ORDER BY records DESC;

-- Q6. Special encodings: unknown and the sentinel -1 (NOT SQL NULL).
SELECT
    SUM(CASE WHEN job = 'unknown' THEN 1 ELSE 0 END) AS job_unknown,
    SUM(CASE WHEN education = 'unknown' THEN 1 ELSE 0 END) AS education_unknown,
    SUM(CASE WHEN contact = 'unknown' THEN 1 ELSE 0 END) AS contact_unknown,
    SUM(CASE WHEN poutcome = 'unknown' THEN 1 ELSE 0 END) AS poutcome_unknown,
    SUM(CASE WHEN pdays = -1 THEN 1 ELSE 0 END) AS pdays_minus_one
FROM bank_marketing;

-- Q7. Age bands: an example of CASE WHEN for business segmentation.
SELECT
    CASE
        WHEN age < 30 THEN 'under_30'
        WHEN age < 45 THEN '30_to_44'
        WHEN age < 60 THEN '45_to_59'
        ELSE '60_plus'
    END AS age_band,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY age_band
ORDER BY FIELD(age_band, 'under_30','30_to_44','45_to_59','60_plus');

-- Q8. Contact-frequency bands: current campaign contact count, associative only.
SELECT
    CASE
        WHEN campaign = 1 THEN '1_contact'
        WHEN campaign = 2 THEN '2_contacts'
        WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
        ELSE '5_plus_contacts'
    END AS campaign_band,
    COUNT(*) AS records,
    SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
    ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
      AS conversion_rate_pct
FROM bank_marketing
GROUP BY campaign_band
ORDER BY FIELD(campaign_band, '1_contact','2_contacts','3_4_contacts','5_plus_contacts');

-- Q9. Example window function: descriptive ranking among sufficiently sized job groups.
WITH job_stats AS (
    SELECT
        job,
        COUNT(*) AS records,
        SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS subscriptions,
        ROUND(100.0 * AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END), 2)
            AS conversion_rate_pct
    FROM bank_marketing
    GROUP BY job
)
SELECT
    job,
    records,
    subscriptions,
    conversion_rate_pct,
    DENSE_RANK() OVER (ORDER BY conversion_rate_pct DESC) AS conversion_rank
FROM job_stats
WHERE records >= 500
ORDER BY conversion_rank, job;

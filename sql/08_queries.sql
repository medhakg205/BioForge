USE bioforge;

-- =========================================================
-- 8.1 Full history of one strain (mutations x treatments)
-- Picks a synthetic strain that has 2+ mutations and treatments.
-- Duplicated rows (mutations x treatments) are expected.
-- =========================================================
SET @sid = (
    SELECT sm.strain_id
    FROM strain_mutation sm
    JOIN treatment t ON t.strain_id = sm.strain_id
    GROUP BY sm.strain_id
    HAVING COUNT(DISTINCT sm.mutation_id) >= 2
    ORDER BY sm.strain_id
    LIMIT 1
);

SELECT s.strain_id, s.species, s.collection_date, h.name AS hospital,
       m.gene_name, m.mutation_type,
       a.name AS antibiotic, t.start_date, o.result, o.resistance_confirmed
FROM strain s
LEFT JOIN hospital h        ON h.hospital_id = s.hospital_id
JOIN strain_mutation sm     ON sm.strain_id = s.strain_id
JOIN mutation m             ON m.mutation_id = sm.mutation_id
LEFT JOIN treatment t       ON t.strain_id = s.strain_id AND t.is_active = TRUE
LEFT JOIN antibiotic a      ON a.antibiotic_id = t.antibiotic_id
LEFT JOIN outcome o         ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
WHERE s.strain_id = @sid AND s.is_active = TRUE
ORDER BY t.start_date, m.gene_name;

-- =========================================================
-- 8.2 Monthly resistance rate per antibiotic (uses the view)
-- =========================================================
SELECT * FROM v_resistance_rate_monthly
ORDER BY antibiotic_name, month_label;

-- =========================================================
-- 8.3 Failure rate per mutation (all antibiotics combined)
-- Threshold 10; lower it if this returns too few rows.
-- =========================================================
SELECT m.gene_name, m.mutation_type,
       COUNT(*) AS total_treatments,
       SUM(o.result IN ('failed','relapsed','deceased')) AS failed_treatments,
       ROUND(100 * SUM(o.result IN ('failed','relapsed','deceased')) / COUNT(*), 2) AS failure_rate_pct
FROM mutation m
JOIN strain_mutation sm ON sm.mutation_id = m.mutation_id
JOIN strain s           ON s.strain_id = sm.strain_id AND s.is_active = TRUE
JOIN treatment t        ON t.strain_id = s.strain_id AND t.is_active = TRUE
JOIN outcome o          ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
GROUP BY m.mutation_id, m.gene_name, m.mutation_type
HAVING total_treatments >= 10
ORDER BY failure_rate_pct DESC;

-- =========================================================
-- EXTRA 1: Literature-expected vs observed failure
-- =========================================================
SELECT m.gene_name, a.name AS antibiotic, maa.effect AS literature_effect,
       COUNT(*) AS total_treatments,
       SUM(o.result IN ('failed','relapsed','deceased')) AS failed,
       ROUND(100 * SUM(o.result IN ('failed','relapsed','deceased')) / COUNT(*), 2) AS observed_failure_pct
FROM mutation_antibiotic_assoc maa
JOIN mutation m         ON m.mutation_id = maa.mutation_id
JOIN antibiotic a       ON a.antibiotic_id = maa.antibiotic_id
JOIN strain_mutation sm ON sm.mutation_id = maa.mutation_id
JOIN treatment t        ON t.strain_id = sm.strain_id
                       AND t.antibiotic_id = maa.antibiotic_id AND t.is_active = TRUE
JOIN outcome o          ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
GROUP BY maa.assoc_id, m.gene_name, a.name, maa.effect
ORDER BY observed_failure_pct DESC;

-- =========================================================
-- EXTRA 2: Lab-only resistance trend (R share per antibiotic per year)
-- Both data sources: 'synthetic' and 'BV-BRC'
-- =========================================================
SELECT data_source, antibiotic, yr,
       COUNT(*) AS tests,
       ROUND(100 * SUM(susceptibility = 'R') / COUNT(*), 2) AS pct_resistant
FROM (
    SELECT s.genomic_metadata->>'$.data_source' AS data_source,
           a.name AS antibiotic,
           YEAR(rp.test_date) AS yr,
           rp.susceptibility
    FROM resistance_phenotype rp
    JOIN strain s     ON s.strain_id = rp.strain_id AND s.is_active = TRUE
    JOIN antibiotic a ON a.antibiotic_id = rp.antibiotic_id
) x
GROUP BY data_source, antibiotic, yr
ORDER BY data_source, antibiotic, yr;

-- =========================================================
-- EXTRA 3: Failure rate per hospital
-- =========================================================
SELECT h.hospital_id, h.name, h.city,
       COUNT(*) AS total_treatments,
       SUM(o.result IN ('failed','relapsed','deceased')) AS failed,
       ROUND(100 * SUM(o.result IN ('failed','relapsed','deceased')) / COUNT(*), 2) AS failure_rate_pct
FROM hospital h
JOIN strain s    ON s.hospital_id = h.hospital_id AND s.is_active = TRUE
JOIN treatment t ON t.strain_id = s.strain_id AND t.is_active = TRUE
JOIN outcome o   ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
WHERE h.is_active = TRUE
GROUP BY h.hospital_id, h.name, h.city
ORDER BY failure_rate_pct DESC;

-- =========================================================
-- EXTRA 4: Strains carrying 2 or more mutations
-- =========================================================
SELECT s.strain_id, COUNT(*) AS mutation_count,
       GROUP_CONCAT(m.gene_name ORDER BY m.gene_name SEPARATOR ', ') AS genes
FROM strain s
JOIN strain_mutation sm ON sm.strain_id = s.strain_id
JOIN mutation m         ON m.mutation_id = sm.mutation_id
WHERE s.is_active = TRUE
GROUP BY s.strain_id
HAVING mutation_count >= 2
ORDER BY mutation_count DESC, s.strain_id;
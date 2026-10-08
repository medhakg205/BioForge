USE bioforge;

-- View 1: resistance rate per antibiotic per month (report query 8.2)
CREATE OR REPLACE VIEW v_resistance_rate_monthly AS
SELECT
    a.antibiotic_id,
    a.name AS antibiotic_name,
    DATE_FORMAT(t.start_date, '%Y-%m') AS month_label,
    COUNT(*) AS total_treatments,
    SUM(o.resistance_confirmed) AS resistant_count,
    ROUND(100 * SUM(o.resistance_confirmed) / COUNT(*), 2) AS resistance_rate_pct
FROM treatment t
JOIN outcome o    ON o.treatment_id = t.treatment_id
JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
JOIN strain s     ON s.strain_id = t.strain_id
WHERE t.is_active = TRUE
  AND o.is_active = TRUE
  AND s.is_active = TRUE
GROUP BY a.antibiotic_id, a.name, DATE_FORMAT(t.start_date, '%Y-%m');

-- View 2: treatment failure rate per mutation and antibiotic (report query 8.3)
-- "failure" = result is failed, relapsed or deceased
CREATE OR REPLACE VIEW v_mutation_treatment_failure AS
SELECT
    m.mutation_id,
    m.gene_name,
    m.mutation_type,
    a.name AS antibiotic_name,
    COUNT(*) AS total_treatments,
    SUM(o.result IN ('failed','relapsed','deceased')) AS failed_treatments,
    ROUND(100 * SUM(o.result IN ('failed','relapsed','deceased')) / COUNT(*), 2) AS failure_rate_pct
FROM mutation m
JOIN strain_mutation sm ON sm.mutation_id = m.mutation_id
JOIN strain s           ON s.strain_id = sm.strain_id
JOIN treatment t        ON t.strain_id = s.strain_id
JOIN outcome o          ON o.treatment_id = t.treatment_id
JOIN antibiotic a       ON a.antibiotic_id = t.antibiotic_id
WHERE s.is_active = TRUE
  AND t.is_active = TRUE
  AND o.is_active = TRUE
GROUP BY m.mutation_id, m.gene_name, m.mutation_type, a.name;
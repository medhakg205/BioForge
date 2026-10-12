-- Performance walkthrough for the separate 50,000-row bioforge_perf database.
-- Requires MySQL 8.0.18+ for EXPLAIN ANALYZE and sql/generate_seed.py --scale.
USE bioforge_perf;

-- Compare a selective antibiotic/date-range query before and after its index.
ALTER TABLE treatment DROP INDEX idx_treatment_composite;
EXPLAIN ANALYZE
SELECT treatment_id, strain_id, start_date
FROM treatment
WHERE antibiotic_id = 1
  AND start_date BETWEEN '2023-01-01' AND '2023-12-31';

CREATE INDEX idx_treatment_composite ON treatment (antibiotic_id, start_date);
EXPLAIN ANALYZE
SELECT treatment_id, strain_id, start_date
FROM treatment
WHERE antibiotic_id = 1
  AND start_date BETWEEN '2023-01-01' AND '2023-12-31';

-- Analytical query 8.2: monthly resistance rate per antibiotic.
EXPLAIN ANALYZE
SELECT a.antibiotic_id, a.name AS antibiotic_name,
       DATE_FORMAT(t.start_date, '%Y-%m') AS month_label,
       COUNT(*) AS total_treatments,
       SUM(o.resistance_confirmed) AS resistant_count,
       ROUND(100 * SUM(o.resistance_confirmed) / COUNT(*), 2) AS resistance_rate_pct
FROM treatment t
JOIN outcome o ON o.treatment_id = t.treatment_id
JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
JOIN strain s ON s.strain_id = t.strain_id
WHERE t.is_active = TRUE
  AND o.is_active = TRUE
  AND s.is_active = TRUE
GROUP BY a.antibiotic_id, a.name, DATE_FORMAT(t.start_date, '%Y-%m');

-- Analytical query 8.3: failure rate per mutation across antibiotics.
EXPLAIN ANALYZE
SELECT m.gene_name, m.mutation_type,
       COUNT(*) AS total_treatments,
       SUM(o.result IN ('failed', 'relapsed', 'deceased')) AS failed_treatments,
       ROUND(100 * SUM(o.result IN ('failed', 'relapsed', 'deceased')) / COUNT(*), 2)
           AS failure_rate_pct
FROM mutation m
JOIN strain_mutation sm ON sm.mutation_id = m.mutation_id
JOIN strain s ON s.strain_id = sm.strain_id AND s.is_active = TRUE
JOIN treatment t ON t.strain_id = s.strain_id AND t.is_active = TRUE
JOIN outcome o ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
GROUP BY m.mutation_id, m.gene_name, m.mutation_type
HAVING total_treatments >= 10
ORDER BY failure_rate_pct DESC;

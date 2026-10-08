USE bioforge;

SELECT '--- 8.1 full strain history ---' AS q;
SET @sid = (SELECT sm.strain_id FROM strain_mutation sm
            JOIN treatment t ON t.strain_id = sm.strain_id
            GROUP BY sm.strain_id HAVING COUNT(DISTINCT sm.mutation_id) >= 2
            ORDER BY sm.strain_id LIMIT 1);
EXPLAIN SELECT s.strain_id, s.species, s.collection_date, h.name AS hospital,
       m.gene_name, m.mutation_type, a.name AS antibiotic, t.start_date, o.result, o.resistance_confirmed
FROM strain s
LEFT JOIN hospital h        ON h.hospital_id = s.hospital_id
JOIN strain_mutation sm     ON sm.strain_id = s.strain_id
JOIN mutation m             ON m.mutation_id = sm.mutation_id
LEFT JOIN treatment t       ON t.strain_id = s.strain_id AND t.is_active = TRUE
LEFT JOIN antibiotic a      ON a.antibiotic_id = t.antibiotic_id
LEFT JOIN outcome o         ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
WHERE s.strain_id = @sid AND s.is_active = TRUE
ORDER BY t.start_date, m.gene_name;

SELECT '--- 8.2 monthly resistance view ---' AS q;
EXPLAIN SELECT * FROM v_resistance_rate_monthly ORDER BY antibiotic_name, month_label;

SELECT '--- 8.3 failure rate per mutation ---' AS q;
EXPLAIN SELECT m.gene_name, m.mutation_type, COUNT(*) AS total_treatments,
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
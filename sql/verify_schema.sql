-- =====================================================================
-- BioForge: verify_schema.sql   (owner: Medha)
-- Run AFTER 01_schema.sql and 04_seed.sql. Screenshot the outputs for
-- the report's "Implementation Results" section.
-- =====================================================================
USE bioforge;

-- 1. All 9 tables exist (expect 9 rows)
SELECT table_name, engine, table_rows
FROM information_schema.tables
WHERE table_schema = 'bioforge' ORDER BY table_name;

-- 2. Row counts (expect roughly: 5 / 20 / 27 / 500 / ~510 / ~1500 / =treatment / ~730 / 46)
SELECT 'hospital' t, COUNT(*) n FROM hospital
UNION ALL SELECT 'antibiotic', COUNT(*) FROM antibiotic
UNION ALL SELECT 'mutation', COUNT(*) FROM mutation
UNION ALL SELECT 'strain', COUNT(*) FROM strain
UNION ALL SELECT 'strain_mutation', COUNT(*) FROM strain_mutation
UNION ALL SELECT 'treatment', COUNT(*) FROM treatment
UNION ALL SELECT 'outcome', COUNT(*) FROM outcome
UNION ALL SELECT 'resistance_phenotype', COUNT(*) FROM resistance_phenotype
UNION ALL SELECT 'mutation_antibiotic_assoc', COUNT(*) FROM mutation_antibiotic_assoc;

-- 3. Every foreign key and its ON DELETE rule (matches ER/EER cardinalities)
SELECT k.table_name, k.column_name, k.referenced_table_name AS references_table,
       r.delete_rule
FROM information_schema.key_column_usage k
JOIN information_schema.referential_constraints r
  ON r.constraint_name = k.constraint_name AND r.constraint_schema = k.table_schema
WHERE k.table_schema = 'bioforge' AND k.referenced_table_name IS NOT NULL
ORDER BY k.table_name;

-- 4. UNIQUE / CHECK constraints (expect uq_mutation_signature, outcome.treatment_id,
--    strain.genome_accession, chk_sm_confidence, ...)
SELECT table_name, constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'bioforge' AND constraint_type IN ('UNIQUE','CHECK')
ORDER BY table_name;

-- 5. Orphan checks: ALL must return 0
SELECT COUNT(*) AS orphan_treatments FROM treatment t
  LEFT JOIN strain s ON s.strain_id = t.strain_id WHERE s.strain_id IS NULL;
SELECT COUNT(*) AS orphan_outcomes FROM outcome o
  LEFT JOIN treatment t ON t.treatment_id = o.treatment_id WHERE t.treatment_id IS NULL;
SELECT COUNT(*) AS orphan_strain_mutations FROM strain_mutation sm
  LEFT JOIN mutation m ON m.mutation_id = sm.mutation_id WHERE m.mutation_id IS NULL;

-- 6. 1:1 Treatment-Outcome (both must be 0)
SELECT COUNT(*) AS treatments_without_outcome FROM treatment t
  LEFT JOIN outcome o ON o.treatment_id = t.treatment_id WHERE o.outcome_id IS NULL;
SELECT COUNT(*) AS treatments_with_multiple_outcomes FROM (
  SELECT treatment_id FROM outcome GROUP BY treatment_id HAVING COUNT(*) > 1) x;

-- 7. Business rule holds in the data (must be 0)
SELECT COUNT(*) AS follow_up_before_start
FROM outcome o JOIN treatment t ON t.treatment_id = o.treatment_id
WHERE o.follow_up_date IS NOT NULL AND o.follow_up_date < t.start_date;

-- 8. JSON column works: query a key inside genomic_metadata
SELECT genomic_metadata->>'$.platform' AS platform, COUNT(*) AS strains
FROM strain GROUP BY platform;

-- 9. Planted pattern #1: ciprofloxacin bad-outcome rate with vs without a gyrA mutation
--    (expect ~60-70% vs ~10%)
SELECT x.carries_gyrA, COUNT(*) AS treatments,
       ROUND(100 * AVG(o.result IN ('failed','relapsed','deceased')), 1) AS pct_bad_outcome
FROM treatment t
JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id AND a.name = 'Ciprofloxacin'
JOIN outcome o ON o.treatment_id = t.treatment_id
JOIN (SELECT s.strain_id,
             COALESCE(MAX(m.gene_name = 'gyrA'), 0) AS carries_gyrA
      FROM strain s
      LEFT JOIN strain_mutation sm ON sm.strain_id = s.strain_id
      LEFT JOIN mutation m ON m.mutation_id = sm.mutation_id
      GROUP BY s.strain_id) x ON x.strain_id = t.strain_id
GROUP BY x.carries_gyrA;

-- 10. Planted pattern #2: confirmed-resistance rate rises by year (expect upward trend)
SELECT YEAR(t.start_date) AS yr, COUNT(*) AS treatments,
       ROUND(100 * AVG(o.resistance_confirmed), 1) AS resistance_confirmed_pct
FROM treatment t JOIN outcome o ON o.treatment_id = t.treatment_id
GROUP BY yr ORDER BY yr;

-- 11. Provenance: which reference associations are source-checked vs not
SELECT CASE WHEN evidence_source LIKE 'Verified%' THEN 'Verified (cited)'
            ELSE 'UNVERIFIED - confirm before citing' END AS status,
       COUNT(*) AS associations
FROM mutation_antibiotic_assoc GROUP BY status;

-- 12. Table-level provenance labels
SELECT table_name, table_comment FROM information_schema.tables
WHERE table_schema = 'bioforge' ORDER BY table_name;

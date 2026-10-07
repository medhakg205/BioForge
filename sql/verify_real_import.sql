-- =====================================================================
-- BioForge: verify_real_import.sql  (owner: Medha)
-- Run AFTER 05_real_import.sql. Screenshot for the report.
-- =====================================================================
USE bioforge;

-- 1. Real vs synthetic strains
SELECT COALESCE(genomic_metadata->>'$.data_source','(unlabelled)') AS data_source,
       COUNT(*) AS strains
FROM strain GROUP BY data_source;

-- 2. Real strains per species and country
SELECT species, geographic_origin, COUNT(*) AS strains
FROM strain WHERE genomic_metadata->>'$.data_source' = 'BV-BRC'
GROUP BY species, geographic_origin ORDER BY strains DESC LIMIT 20;

-- 3. REAL lab resistance rate per antibiotic (S/I/R from published AST)
SELECT a.name AS antibiotic, COUNT(*) AS tests,
       SUM(rp.susceptibility = 'R') AS resistant,
       ROUND(100 * AVG(rp.susceptibility = 'R'), 1) AS resistant_pct
FROM resistance_phenotype rp
JOIN strain s ON s.strain_id = rp.strain_id
JOIN antibiotic a ON a.antibiotic_id = rp.antibiotic_id
WHERE s.genomic_metadata->>'$.data_source' = 'BV-BRC'
GROUP BY a.name HAVING tests >= 10 ORDER BY resistant_pct DESC;

-- 4. REAL resistance trend by year (lab-only, no treatment needed)
SELECT YEAR(s.collection_date) AS yr, COUNT(*) AS tests,
       ROUND(100 * AVG(rp.susceptibility = 'R'), 1) AS resistant_pct
FROM resistance_phenotype rp
JOIN strain s ON s.strain_id = rp.strain_id
WHERE s.genomic_metadata->>'$.data_source' = 'BV-BRC'
GROUP BY yr ORDER BY yr;

-- 5. Integrity: no orphan phenotypes (must be 0)
SELECT COUNT(*) AS orphan_phenotypes FROM resistance_phenotype rp
LEFT JOIN strain s ON s.strain_id = rp.strain_id WHERE s.strain_id IS NULL;

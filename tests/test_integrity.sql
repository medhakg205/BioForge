USE bioforge;

SELECT '1. FK: treatment with non-existent strain -> expect ERROR 1452' AS test;
INSERT INTO treatment (strain_id, antibiotic_id, start_date)
VALUES (999999999, (SELECT MIN(antibiotic_id) FROM antibiotic), '2024-01-01');

SELECT '2. UNIQUE: second outcome for same treatment -> expect ERROR 1062' AS test;
INSERT INTO outcome (treatment_id, result)
SELECT treatment_id, 'cured' FROM outcome ORDER BY outcome_id LIMIT 1;

SELECT '3. UNIQUE: duplicate mutation signature -> expect ERROR 1062' AS test;
INSERT INTO mutation (gene_name, mutation_type, genome_position, ref_allele, alt_allele)
SELECT gene_name, mutation_type, genome_position, ref_allele, alt_allele
FROM mutation
WHERE genome_position IS NOT NULL AND ref_allele IS NOT NULL AND alt_allele IS NOT NULL
LIMIT 1;

SELECT '4. CHECK: confidence_score = 1.5 -> expect ERROR 3819' AS test;
UPDATE strain_mutation SET confidence_score = 1.5 LIMIT 1;

SELECT '5. TRIGGER: follow-up before treatment start -> expect ERROR 1644' AS test;
UPDATE outcome SET follow_up_date = '1900-01-01' WHERE outcome_id = 1;

SELECT '6. UNIQUE: duplicate genome_accession -> expect ERROR 1062' AS test;
INSERT INTO strain (species, collection_date, genome_accession)
SELECT 'Escherichia coli', '2024-01-01', genome_accession
FROM strain WHERE genome_accession IS NOT NULL LIMIT 1;

SELECT '7. ENUM: invalid result value -> expect ERROR 1265' AS test;
UPDATE outcome SET result = 'unknown' WHERE outcome_id = 1;

SELECT '8. POSITIVE CONTROL: valid update inside a transaction -> expect success' AS test;
START TRANSACTION;
UPDATE outcome SET notes = 'integrity test' WHERE outcome_id = 1;
ROLLBACK;

SELECT 'DONE' AS test;

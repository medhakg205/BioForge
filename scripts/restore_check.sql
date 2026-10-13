-- restore_check.sql
-- Verify that the restored database matches the original
-- Run this after restoring `bioforge_backup.sql` into `bioforge_restore`
-- It prints a simple report of row counts per table.

SELECT 'hospital' AS table_name,
       (SELECT COUNT(*) FROM bioforge.hospital) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.hospital) AS restored_cnt;
SELECT 'antibiotic' AS table_name,
       (SELECT COUNT(*) FROM bioforge.antibiotic) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.antibiotic) AS restored_cnt;
SELECT 'strain' AS table_name,
       (SELECT COUNT(*) FROM bioforge.strain) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.strain) AS restored_cnt;
SELECT 'mutation' AS table_name,
       (SELECT COUNT(*) FROM bioforge.mutation) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.mutation) AS restored_cnt;
SELECT 'strain_mutation' AS table_name,
       (SELECT COUNT(*) FROM bioforge.strain_mutation) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.strain_mutation) AS restored_cnt;
SELECT 'treatment' AS table_name,
       (SELECT COUNT(*) FROM bioforge.treatment) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.treatment) AS restored_cnt;
SELECT 'outcome' AS table_name,
       (SELECT COUNT(*) FROM bioforge.outcome) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.outcome) AS restored_cnt;
SELECT 'resistance_phenotype' AS table_name,
       (SELECT COUNT(*) FROM bioforge.resistance_phenotype) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.resistance_phenotype) AS restored_cnt;
SELECT 'mutation_antibiotic_assoc' AS table_name,
       (SELECT COUNT(*) FROM bioforge.mutation_antibiotic_assoc) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.mutation_antibiotic_assoc) AS restored_cnt;
SELECT 'audit_log' AS table_name,
       (SELECT COUNT(*) FROM bioforge.audit_log) AS original_cnt,
       (SELECT COUNT(*) FROM bioforge_restore.audit_log) AS restored_cnt;

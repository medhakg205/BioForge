-- BioForge transaction/concurrency walkthrough for MySQL Workbench.
-- Open two connections to bioforge and follow each session's steps in order.
-- Use a seeded strain_id and antibiotic_id for tests that insert a treatment.

-- T1: sp_record_treatment rolls back its treatment insert when the outcome
-- trigger rejects a follow-up date before the treatment start.
-- Session A:
CALL sp_record_treatment(1, 1, 500, 7, '2025-01-10', 'T1 test',
                         'cured', FALSE, '2025-01-09', NULL);
-- Expect the trigger error from trg_outcome_followup_ins.
-- Session B (after Session A returns the error):
SELECT COUNT(*) FROM treatment WHERE prescribing_physician = 'T1 test';
-- The count is zero because the procedure's SQLEXCEPTION handler rolled back.

-- T2: REPEATABLE READ keeps the first consistent read stable across commits.
-- Session A:
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT COUNT(*) AS initial_count FROM treatment WHERE antibiotic_id = 1;
-- Session B:
START TRANSACTION;
INSERT INTO treatment
    (strain_id, antibiotic_id, dosage_mg, duration_days, start_date, prescribing_physician)
VALUES (1, 1, 500, 7, CURDATE(), 'T2 test');
SET @t2_id = LAST_INSERT_ID();
INSERT INTO outcome (treatment_id, result, follow_up_date)
VALUES (@t2_id, 'cured', DATE_ADD(CURDATE(), INTERVAL 7 DAY));
COMMIT;
-- Session A:
SELECT COUNT(*) AS repeated_count FROM treatment WHERE antibiotic_id = 1;
-- The counts are equal within Session A's transaction.
COMMIT;
SELECT COUNT(*) AS after_commit_count FROM treatment WHERE antibiotic_id = 1;
-- Optional cleanup as an administrator: delete the outcome and treatment for
-- prescribing_physician = 'T2 test'.

-- T3: SELECT ... FOR UPDATE blocks a conflicting update until Session A commits.
-- Session A:
START TRANSACTION;
SELECT treatment_id FROM treatment WHERE treatment_id = 1 FOR UPDATE;
-- Session B: UPDATE treatment SET dosage_mg = dosage_mg + 1
--            WHERE treatment_id = 1; (waits for Session A)
-- Session A:
UPDATE treatment SET dosage_mg = dosage_mg + 1 WHERE treatment_id = 1;
COMMIT;
-- Session B's waiting update then completes; COMMIT in Session B.

-- T4: READ COMMITTED sees a newly committed row on the next statement.
-- Session A:
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT COUNT(*) AS initial_count FROM treatment WHERE antibiotic_id = 2;
-- Session B:
START TRANSACTION;
INSERT INTO treatment
    (strain_id, antibiotic_id, dosage_mg, duration_days, start_date, prescribing_physician)
VALUES (1, 2, 500, 7, CURDATE(), 'T4 test');
SET @t4_id = LAST_INSERT_ID();
INSERT INTO outcome (treatment_id, result, follow_up_date)
VALUES (@t4_id, 'cured', DATE_ADD(CURDATE(), INTERVAL 7 DAY));
COMMIT;
-- Session A:
SELECT COUNT(*) AS refreshed_count FROM treatment WHERE antibiotic_id = 2;
-- refreshed_count includes Session B's committed row.
COMMIT;
-- Optional cleanup as an administrator: delete the outcome and treatment for
-- prescribing_physician = 'T4 test'.

-- T5: Deliberately create a deadlock and observe InnoDB abort one transaction.
-- Session A:
START TRANSACTION;
UPDATE treatment SET dosage_mg = dosage_mg + 1 WHERE treatment_id = 1;
-- Session B:
START TRANSACTION;
UPDATE treatment SET dosage_mg = dosage_mg + 1 WHERE treatment_id = 2;
-- Session A:
UPDATE treatment SET dosage_mg = dosage_mg + 1 WHERE treatment_id = 2;
-- Session B: this statement waits for treatment_id=1 and completes a deadlock:
UPDATE treatment SET dosage_mg = dosage_mg + 1 WHERE treatment_id = 1;
-- InnoDB returns error 1213 for one session. Roll back the surviving session.
ROLLBACK;

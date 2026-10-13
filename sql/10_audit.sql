USE bioforge;

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id  BIGINT UNSIGNED NOT NULL,
    `action`   ENUM('UPDATE', 'SOFT_DELETE') NOT NULL,
    old_values JSON NOT NULL,
    new_values JSON NOT NULL,
    changed_by VARCHAR(288) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_table_record (table_name, record_id)
) ENGINE=InnoDB;

DROP TRIGGER IF EXISTS trg_treatment_audit;
DROP TRIGGER IF EXISTS trg_outcome_audit;

DELIMITER $$

CREATE TRIGGER trg_treatment_audit
AFTER UPDATE ON treatment
FOR EACH ROW
BEGIN
    INSERT INTO audit_log
        (table_name, record_id, `action`, old_values, new_values, changed_by)
    VALUES
        ('treatment', NEW.treatment_id,
         IF(OLD.is_active = TRUE AND NEW.is_active = FALSE, 'SOFT_DELETE', 'UPDATE'),
         JSON_OBJECT(
             'treatment_id', OLD.treatment_id,
             'strain_id', OLD.strain_id,
             'antibiotic_id', OLD.antibiotic_id,
             'dosage_mg', OLD.dosage_mg,
             'duration_days', OLD.duration_days,
             'start_date', OLD.start_date,
             'prescribing_physician', OLD.prescribing_physician,
             'created_at', OLD.created_at,
             'updated_at', OLD.updated_at,
             'is_active', OLD.is_active,
             'deleted_at', OLD.deleted_at
         ),
         JSON_OBJECT(
             'treatment_id', NEW.treatment_id,
             'strain_id', NEW.strain_id,
             'antibiotic_id', NEW.antibiotic_id,
             'dosage_mg', NEW.dosage_mg,
             'duration_days', NEW.duration_days,
             'start_date', NEW.start_date,
             'prescribing_physician', NEW.prescribing_physician,
             'created_at', NEW.created_at,
             'updated_at', NEW.updated_at,
             'is_active', NEW.is_active,
             'deleted_at', NEW.deleted_at
         ),
         CURRENT_USER());
END$$

CREATE TRIGGER trg_outcome_audit
AFTER UPDATE ON outcome
FOR EACH ROW
BEGIN
    INSERT INTO audit_log
        (table_name, record_id, `action`, old_values, new_values, changed_by)
    VALUES
        ('outcome', NEW.outcome_id,
         IF(OLD.is_active = TRUE AND NEW.is_active = FALSE, 'SOFT_DELETE', 'UPDATE'),
         JSON_OBJECT(
             'outcome_id', OLD.outcome_id,
             'treatment_id', OLD.treatment_id,
             'result', OLD.result,
             'resistance_confirmed', OLD.resistance_confirmed,
             'follow_up_date', OLD.follow_up_date,
             'notes', OLD.notes,
             'created_at', OLD.created_at,
             'updated_at', OLD.updated_at,
             'is_active', OLD.is_active,
             'deleted_at', OLD.deleted_at
         ),
         JSON_OBJECT(
             'outcome_id', NEW.outcome_id,
             'treatment_id', NEW.treatment_id,
             'result', NEW.result,
             'resistance_confirmed', NEW.resistance_confirmed,
             'follow_up_date', NEW.follow_up_date,
             'notes', NEW.notes,
             'created_at', NEW.created_at,
             'updated_at', NEW.updated_at,
             'is_active', NEW.is_active,
             'deleted_at', NEW.deleted_at
         ),
         CURRENT_USER());
END$$

DELIMITER ;

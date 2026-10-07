USE bioforge;

DROP TRIGGER IF EXISTS trg_outcome_followup_ins;
DROP TRIGGER IF EXISTS trg_outcome_followup_upd;
DROP TRIGGER IF EXISTS trg_strain_softdelete;
DROP TRIGGER IF EXISTS trg_treatment_softdelete;
DROP TRIGGER IF EXISTS trg_outcome_softdelete;

DELIMITER $$

-- Reject outcomes whose follow_up_date is before the treatment start_date
CREATE TRIGGER trg_outcome_followup_ins
BEFORE INSERT ON outcome
FOR EACH ROW
BEGIN
  DECLARE v_start DATE;
  IF NEW.follow_up_date IS NOT NULL THEN
    SELECT start_date INTO v_start FROM treatment WHERE treatment_id = NEW.treatment_id;
    IF v_start IS NOT NULL AND NEW.follow_up_date < v_start THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'follow_up_date cannot be earlier than treatment start_date';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_outcome_followup_upd
BEFORE UPDATE ON outcome
FOR EACH ROW
BEGIN
  DECLARE v_start DATE;
  IF NEW.follow_up_date IS NOT NULL THEN
    SELECT start_date INTO v_start FROM treatment WHERE treatment_id = NEW.treatment_id;
    IF v_start IS NOT NULL AND NEW.follow_up_date < v_start THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'follow_up_date cannot be earlier than treatment start_date';
    END IF;
  END IF;
END$$

-- Soft delete: set/clear deleted_at when is_active changes
CREATE TRIGGER trg_strain_softdelete
BEFORE UPDATE ON strain
FOR EACH ROW
BEGIN
  IF NEW.is_active = 0 AND OLD.is_active = 1 THEN
    SET NEW.deleted_at = CURRENT_TIMESTAMP;
  ELSEIF NEW.is_active = 1 AND OLD.is_active = 0 THEN
    SET NEW.deleted_at = NULL;
  END IF;
END$$

CREATE TRIGGER trg_treatment_softdelete
BEFORE UPDATE ON treatment
FOR EACH ROW
BEGIN
  IF NEW.is_active = 0 AND OLD.is_active = 1 THEN
    SET NEW.deleted_at = CURRENT_TIMESTAMP;
  ELSEIF NEW.is_active = 1 AND OLD.is_active = 0 THEN
    SET NEW.deleted_at = NULL;
  END IF;
END$$

CREATE TRIGGER trg_outcome_softdelete
BEFORE UPDATE ON outcome
FOR EACH ROW
BEGIN
  IF NEW.is_active = 0 AND OLD.is_active = 1 THEN
    SET NEW.deleted_at = CURRENT_TIMESTAMP;
  ELSEIF NEW.is_active = 1 AND OLD.is_active = 0 THEN
    SET NEW.deleted_at = NULL;
  END IF;
END$$

DELIMITER ;

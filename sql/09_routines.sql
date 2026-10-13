USE bioforge;

DROP PROCEDURE IF EXISTS sp_record_treatment;
DROP FUNCTION IF EXISTS fn_failure_rate;

DELIMITER $$

CREATE PROCEDURE sp_record_treatment(
    IN p_strain_id BIGINT UNSIGNED,
    IN p_antibiotic_id INT UNSIGNED,
    IN p_dosage_mg DECIMAL(8,2),
    IN p_duration_days INT UNSIGNED,
    IN p_start_date DATE,
    IN p_prescribing_physician VARCHAR(150),
    IN p_result VARCHAR(20),
    IN p_resistance_confirmed BOOLEAN,
    IN p_follow_up_date DATE,
    IN p_notes TEXT
)
MODIFIES SQL DATA
BEGIN
    DECLARE p_treatment_id BIGINT UNSIGNED;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    INSERT INTO treatment
        (strain_id, antibiotic_id, dosage_mg, duration_days, start_date, prescribing_physician)
    VALUES
        (p_strain_id, p_antibiotic_id, p_dosage_mg, p_duration_days,
         p_start_date, p_prescribing_physician);

    SET p_treatment_id = LAST_INSERT_ID();

    INSERT INTO outcome
        (treatment_id, result, resistance_confirmed, follow_up_date, notes)
    VALUES
        (p_treatment_id, p_result, p_resistance_confirmed, p_follow_up_date, p_notes);

    COMMIT;

    SELECT p_treatment_id AS treatment_id;
END$$

CREATE FUNCTION fn_failure_rate(
    p_gene VARCHAR(100),
    p_antibiotic VARCHAR(100)
)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_failure_rate DECIMAL(5,2);

    SELECT COALESCE(
               ROUND(
                   100 * COUNT(DISTINCT CASE
                       WHEN o.result IN ('failed', 'relapsed', 'deceased')
                       THEN t.treatment_id
                   END) / NULLIF(COUNT(DISTINCT t.treatment_id), 0),
                   2
               ),
               0.00
           )
      INTO v_failure_rate
      FROM mutation m
      JOIN strain_mutation sm ON sm.mutation_id = m.mutation_id
      JOIN strain s ON s.strain_id = sm.strain_id
      JOIN treatment t ON t.strain_id = s.strain_id
      JOIN outcome o ON o.treatment_id = t.treatment_id
      JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
     WHERE m.gene_name = p_gene
       AND a.name = p_antibiotic
       AND s.is_active = TRUE
       AND t.is_active = TRUE
       AND o.is_active = TRUE;

    RETURN v_failure_rate;
END$$

DELIMITER ;

GRANT EXECUTE ON PROCEDURE bioforge.sp_record_treatment
    TO 'bioforge_clinician'@'%';
GRANT EXECUTE ON PROCEDURE bioforge.sp_record_treatment
    TO 'bioforge_clinician'@'localhost';

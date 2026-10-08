USE bioforge;

-- Researcher-safe view: hides prescribing_physician and inactive rows
CREATE OR REPLACE VIEW v_treatment_deidentified AS
SELECT treatment_id, strain_id, antibiotic_id, dosage_mg, duration_days, start_date
FROM treatment
WHERE is_active = 1;

DROP USER IF EXISTS 'bioforge_clinician'@'localhost';
DROP USER IF EXISTS 'bioforge_researcher'@'localhost';
DROP USER IF EXISTS 'bioforge_admin'@'localhost';
DROP USER IF EXISTS 'bioforge_etl'@'localhost';

-- Demo passwords for local testing only. Change them for any real use.
CREATE USER 'bioforge_clinician'@'localhost'  IDENTIFIED BY 'Bf_Clinician#1';
CREATE USER 'bioforge_researcher'@'localhost' IDENTIFIED BY 'Bf_Researcher#1';
CREATE USER 'bioforge_admin'@'localhost'      IDENTIFIED BY 'Bf_Admin#1';
CREATE USER 'bioforge_etl'@'localhost'        IDENTIFIED BY 'Bf_Etl#1';

-- Clinician: read everything, write clinical tables only
GRANT SELECT ON bioforge.* TO 'bioforge_clinician'@'localhost';
GRANT INSERT, UPDATE ON bioforge.treatment            TO 'bioforge_clinician'@'localhost';
GRANT INSERT, UPDATE ON bioforge.outcome              TO 'bioforge_clinician'@'localhost';
GRANT INSERT, UPDATE ON bioforge.resistance_phenotype TO 'bioforge_clinician'@'localhost';

-- Researcher: read only, NO access to the treatment base table
GRANT SELECT ON bioforge.v_treatment_deidentified   TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.hospital                   TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.antibiotic                 TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.strain                     TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.mutation                   TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.strain_mutation            TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.outcome                    TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.resistance_phenotype       TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.mutation_antibiotic_assoc  TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.v_resistance_rate_monthly      TO 'bioforge_researcher'@'localhost';
GRANT SELECT ON bioforge.v_mutation_treatment_failure   TO 'bioforge_researcher'@'localhost';

-- Admin: everything on the bioforge database
GRANT ALL PRIVILEGES ON bioforge.* TO 'bioforge_admin'@'localhost';

-- ETL: insert only
GRANT INSERT ON bioforge.strain          TO 'bioforge_etl'@'localhost';
GRANT INSERT ON bioforge.mutation        TO 'bioforge_etl'@'localhost';
GRANT INSERT ON bioforge.strain_mutation TO 'bioforge_etl'@'localhost';

FLUSH PRIVILEGES;

-- Design note: MySQL has no row-level security, so "clinicians see only their own
-- hospital" is an APPLICATION-LEVEL rule (the app adds WHERE hospital_id = ...).

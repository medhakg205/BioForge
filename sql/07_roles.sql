USE bioforge;

-- Researcher-safe view: hides prescribing_physician and inactive rows
CREATE OR REPLACE VIEW v_treatment_deidentified AS
SELECT treatment_id, strain_id, antibiotic_id, dosage_mg, duration_days, start_date
FROM treatment
WHERE is_active = 1;

DROP USER IF EXISTS 'bioforge_clinician'@'localhost';
DROP USER IF EXISTS 'bioforge_clinician'@'%';
DROP USER IF EXISTS 'bioforge_researcher'@'localhost';
DROP USER IF EXISTS 'bioforge_admin'@'localhost';
DROP USER IF EXISTS 'bioforge_etl'@'localhost';

-- Development credentials only. Restrict '%' accounts and change credentials in real deployments.
CREATE USER 'bioforge_clinician'@'localhost'  IDENTIFIED BY 'Bf_Clinician#1';
CREATE USER 'bioforge_clinician'@'%'          IDENTIFIED BY 'Bf_Clinician#1';
CREATE USER 'bioforge_researcher'@'localhost' IDENTIFIED BY 'Bf_Researcher#1';
CREATE USER 'bioforge_admin'@'localhost'      IDENTIFIED BY 'Bf_Admin#1';
CREATE USER 'bioforge_etl'@'localhost'        IDENTIFIED BY 'Bf_Etl#1';

-- Clinician: read application data, but never the audit trail; write clinical tables only.
GRANT SELECT ON bioforge.hospital TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.antibiotic TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.strain TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.mutation TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.strain_mutation TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.treatment TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.outcome TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.resistance_phenotype TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.mutation_antibiotic_assoc TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.v_treatment_deidentified TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.v_resistance_rate_monthly TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT SELECT ON bioforge.v_mutation_treatment_failure TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT INSERT, UPDATE ON bioforge.treatment TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT INSERT, UPDATE ON bioforge.outcome TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';
GRANT INSERT, UPDATE ON bioforge.resistance_phenotype TO
    'bioforge_clinician'@'localhost', 'bioforge_clinician'@'%';

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

-- Design note: MySQL has no row-level security, so hospital filtering is an
-- APPLICATION-LEVEL control (the app filters by hospital_id).

-- =====================================================================
-- BioForge: 01_schema.sql   (owner: Medha)
-- MySQL 8.0.16+ required (CHECK constraints are enforced from 8.0.16)
-- Rebuilds the whole database from scratch. Run FIRST.
-- =====================================================================

DROP DATABASE IF EXISTS bioforge;
CREATE DATABASE bioforge CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE bioforge;

-- ---------------------------------------------------------------------
-- 1. hospital  (submitting site for strains)
-- ---------------------------------------------------------------------
CREATE TABLE hospital (
    hospital_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    country      VARCHAR(100) NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                 ON UPDATE CURRENT_TIMESTAMP,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at   TIMESTAMP NULL DEFAULT NULL,
    UNIQUE KEY uq_hospital_name_city (name, city)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. antibiotic  (reference table)
-- ---------------------------------------------------------------------
CREATE TABLE antibiotic (
    antibiotic_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    drug_class    VARCHAR(100) NOT NULL,
    route         VARCHAR(30),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. strain  (central entity; JSON column for variable genomic metadata)
-- ---------------------------------------------------------------------
CREATE TABLE strain (
    strain_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hospital_id       INT UNSIGNED,
    species           VARCHAR(150) NOT NULL,
    isolate_source    VARCHAR(100),
    collection_date   DATE NOT NULL,
    geographic_origin VARCHAR(150),
    genome_accession  VARCHAR(50) UNIQUE,
    genomic_metadata  JSON,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                      ON UPDATE CURRENT_TIMESTAMP,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at        TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_strain_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital(hospital_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. mutation  (unique on its biological signature)
-- ---------------------------------------------------------------------
CREATE TABLE mutation (
    mutation_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    gene_name       VARCHAR(100) NOT NULL,
    mutation_type   ENUM('SNP','insertion','deletion','frameshift',
                         'duplication','inversion') NOT NULL,
    genome_position INT UNSIGNED,
    ref_allele      VARCHAR(50),
    alt_allele      VARCHAR(50),
    description     TEXT,
    UNIQUE KEY uq_mutation_signature
        (gene_name, genome_position, ref_allele, alt_allele)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. strain_mutation  (M:N junction with per-detection metadata)
-- ---------------------------------------------------------------------
CREATE TABLE strain_mutation (
    strain_id         BIGINT UNSIGNED NOT NULL,
    mutation_id       BIGINT UNSIGNED NOT NULL,
    detection_date    DATE NOT NULL,
    sequencing_method VARCHAR(50),
    confidence_score  DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    PRIMARY KEY (strain_id, mutation_id),
    CONSTRAINT fk_sm_strain FOREIGN KEY (strain_id)
        REFERENCES strain(strain_id) ON DELETE CASCADE,
    CONSTRAINT fk_sm_mutation FOREIGN KEY (mutation_id)
        REFERENCES mutation(mutation_id) ON DELETE RESTRICT,
    CONSTRAINT chk_sm_confidence CHECK (confidence_score BETWEEN 0 AND 1)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. treatment
--    NOTE: idx_treatment_composite is defined here exactly as in the
--    report (Section 7.2). Tanya's 02_indexes.sql must NOT recreate it.
-- ---------------------------------------------------------------------
CREATE TABLE treatment (
    treatment_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    strain_id             BIGINT UNSIGNED NOT NULL,
    antibiotic_id         INT UNSIGNED NOT NULL,
    dosage_mg             DECIMAL(8,2),
    duration_days         INT UNSIGNED,
    start_date            DATE NOT NULL,
    prescribing_physician VARCHAR(150),
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at            TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_treatment_strain FOREIGN KEY (strain_id)
        REFERENCES strain(strain_id) ON DELETE CASCADE,
    CONSTRAINT fk_treatment_antibiotic FOREIGN KEY (antibiotic_id)
        REFERENCES antibiotic(antibiotic_id) ON DELETE RESTRICT,
    INDEX idx_treatment_composite (antibiotic_id, start_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. outcome  (exactly one per treatment: UNIQUE on treatment_id)
-- ---------------------------------------------------------------------
CREATE TABLE outcome (
    outcome_id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    treatment_id         BIGINT UNSIGNED NOT NULL UNIQUE,
    result               ENUM('cured','failed','relapsed','deceased','ongoing')
                         NOT NULL,
    resistance_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    follow_up_date       DATE,
    notes                TEXT,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                         ON UPDATE CURRENT_TIMESTAMP,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at           TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_outcome_treatment FOREIGN KEY (treatment_id)
        REFERENCES treatment(treatment_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 8. resistance_phenotype  (lab-only testing, independent of treatment)
-- ---------------------------------------------------------------------
CREATE TABLE resistance_phenotype (
    phenotype_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    strain_id      BIGINT UNSIGNED NOT NULL,
    antibiotic_id  INT UNSIGNED NOT NULL,
    mic_value      DECIMAL(8,3),                      -- mg/L
    susceptibility ENUM('S','I','R') NOT NULL,        -- S/I/R categories
    test_method    ENUM('MIC','disk_diffusion','E-test','automated')
                   NOT NULL DEFAULT 'MIC',
    test_date      DATE NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_phenotype_test
        (strain_id, antibiotic_id, test_method, test_date),
    CONSTRAINT fk_rp_strain FOREIGN KEY (strain_id)
        REFERENCES strain(strain_id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_antibiotic FOREIGN KEY (antibiotic_id)
        REFERENCES antibiotic(antibiotic_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 9. mutation_antibiotic_assoc  (literature-known associations)
-- ---------------------------------------------------------------------
CREATE TABLE mutation_antibiotic_assoc (
    assoc_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mutation_id     BIGINT UNSIGNED NOT NULL,
    antibiotic_id   INT UNSIGNED NOT NULL,
    effect          ENUM('resistance','reduced_susceptibility','susceptibility')
                    NOT NULL DEFAULT 'resistance',
    evidence_source VARCHAR(255),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_assoc (mutation_id, antibiotic_id),
    CONSTRAINT fk_maa_mutation FOREIGN KEY (mutation_id)
        REFERENCES mutation(mutation_id) ON DELETE CASCADE,
    CONSTRAINT fk_maa_antibiotic FOREIGN KEY (antibiotic_id)
        REFERENCES antibiotic(antibiotic_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- DATA PROVENANCE LABELS (shown in information_schema.tables)
-- ---------------------------------------------------------------------
ALTER TABLE antibiotic                COMMENT = 'Reference data: real antibiotic names/classes';
ALTER TABLE mutation                  COMMENT = 'Reference data: real gene/variant names; see mutation_antibiotic_assoc.evidence_source for verified vs UNVERIFIED';
ALTER TABLE mutation_antibiotic_assoc COMMENT = 'Reference data: evidence_source marks Verified (cited) vs UNVERIFIED entries';
ALTER TABLE hospital                  COMMENT = 'SYNTHETIC demo data (fictional hospitals)';
ALTER TABLE strain                    COMMENT = 'SYNTHETIC demo data';
ALTER TABLE strain_mutation           COMMENT = 'SYNTHETIC demo data';
ALTER TABLE treatment                 COMMENT = 'SYNTHETIC demo data';
ALTER TABLE outcome                   COMMENT = 'SYNTHETIC demo data';
ALTER TABLE resistance_phenotype      COMMENT = 'SYNTHETIC demo data';

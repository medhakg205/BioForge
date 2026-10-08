USE bioforge;

CREATE INDEX idx_treatment_composite ON treatment (antibiotic_id, start_date);
DROP INDEX tmp_fk_antibiotic ON treatment;

CREATE INDEX idx_mutation_gene ON mutation (gene_name);
CREATE INDEX idx_mutation_type ON mutation (mutation_type);
CREATE INDEX idx_strain_mutation_detection ON strain_mutation (detection_date);
CREATE INDEX idx_phenotype_abx_date ON resistance_phenotype (antibiotic_id, test_date);
DROP INDEX tmp_fk_phenotype_antibiotic ON resistance_phenotype;

ALTER TABLE strain
  ADD INDEX idx_strain_platform (sequencing_platform),
  ADD INDEX idx_strain_data_source (data_source);
USE bioforge;

CREATE INDEX tmp_fk_antibiotic ON treatment (antibiotic_id);
CREATE INDEX tmp_fk_phenotype_antibiotic ON resistance_phenotype (antibiotic_id);

DROP INDEX idx_treatment_composite ON treatment;
DROP INDEX idx_mutation_gene ON mutation;
DROP INDEX idx_mutation_type ON mutation;
DROP INDEX idx_strain_mutation_detection ON strain_mutation;
DROP INDEX idx_phenotype_abx_date ON resistance_phenotype;
ALTER TABLE strain DROP INDEX idx_strain_platform, DROP INDEX idx_strain_data_source;
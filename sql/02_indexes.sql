USE bioforge;

CREATE INDEX idx_mutation_gene ON mutation (gene_name);
CREATE INDEX idx_mutation_type ON mutation (mutation_type);
CREATE INDEX idx_strain_mutation_detection ON strain_mutation (detection_date);
CREATE INDEX idx_phenotype_abx_date ON resistance_phenotype (antibiotic_id, test_date);

ALTER TABLE strain
  ADD COLUMN sequencing_platform VARCHAR(50)
    GENERATED ALWAYS AS (genomic_metadata->>'$.platform') STORED,
  ADD COLUMN data_source VARCHAR(20)
    GENERATED ALWAYS AS (genomic_metadata->>'$.data_source') STORED,
  ADD INDEX idx_strain_platform (sequencing_platform),
  ADD INDEX idx_strain_data_source (data_source);

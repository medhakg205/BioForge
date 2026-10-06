# BioForge: how to run everything (Medha's part)

## 0. What you need installed
1. **MySQL Server 8.0.16 or newer** (+ MySQL Workbench). Windows: MySQL Installer from mysql.com
   -> choose "Server only" + "Workbench". Remember the **root password** you set.
2. **Python 3.8+** from python.org (tick "Add Python to PATH" on Windows).
   Check: open a terminal and run `python --version` (Windows) or `python3 --version` (Mac/Linux).
   No Python packages need installing.

## 1. Put the files in one folder
```
bioforge/
  sql/
    01_schema.sql   generate_seed.py   04_seed.sql   verify_schema.sql
    import_real_strains.py   verify_real_import.sql
```
Open a terminal **inside** `bioforge/sql/` (Windows: open the folder, click the address bar,
type `cmd`, Enter).

## 2. Build the database (synthetic + reference data)
Easiest (works in cmd, PowerShell, Mac, Linux), using the MySQL client's `source` command:
```
mysql -u root -p
```
enter the password, then inside the `mysql>` prompt:
```
source 01_schema.sql
source 04_seed.sql
source verify_schema.sql
```
(If `mysql` is "not recognised" on Windows, use the full path, e.g.
`"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p`.
Do **not** use `mysql ... < file.sql` in PowerShell; `<` does not work there. Use the
`source` way above or cmd.exe.)

Workbench alternative: File -> Open SQL Script -> pick the file -> click the lightning
bolt. Run `01_schema.sql`, then `04_seed.sql`, then `verify_schema.sql`.

WARNING: `01_schema.sql` starts with `DROP DATABASE IF EXISTS bioforge;` It wipes and
rebuilds the database every time. Always re-run 04 (and 05) afterwards.

`04_seed.sql` is already generated. Only run `python generate_seed.py` if you edit the
generator; it rewrites `04_seed.sql`.

## 3. Add REAL strains from BV-BRC
**a) Download the AMR phenotype file** (tab-delimited, real lab susceptibility results):
`ftp://ftp.bvbrc.org/RELEASE_NOTES/PATRIC_genomes_AMR.txt`
(browser or an FTP client such as FileZilla; the file name may differ slightly, e.g.
`PATRIC_genome_AMR.txt`. Use whatever is in that folder.)

**b) Download the genome metadata** from https://www.bv-brc.org : go to Genomes, filter
to the species you want that have AMR phenotype data, and use the download option to
export a **CSV** that includes these columns: Genome ID, Genome Name, Collection Date,
Isolation Country, Isolation Source, Assembly Accession. (The website layout changes;
look for the Download / CSV button and tick those columns.) Alternatively use the
`genome_summary` file in the same FTP folder.
Do **not** open and re-save these files in Excel (it corrupts Genome IDs like `511145.12`).

**c) Convert to SQL:**
```
python import_real_strains.py --amr PATRIC_genomes_AMR.txt --genomes genomes.csv --per-species 60
```
(`python3` on Mac/Linux.) It prints how many strains/phenotypes it imported and how many
rows it skipped and why. If it says a column is missing, it shows the columns it found;
tell your teammate/me and adjust `ALIASES` at the top of the script.

**d) Load it:** in the `mysql>` prompt: `source 05_real_import.sql` then
`source verify_real_import.sql`.

Real strains get ids 100001+, so they never clash with the synthetic ones (1-500). They are
labelled `genomic_metadata->>'$.data_source' = 'BV-BRC'`; synthetic ones say `synthetic`.

## 4. Run order for the whole team
`01_schema.sql` -> (Tanya: `02_indexes.sql`, `03_triggers.sql`) -> `04_seed.sql` ->
`05_real_import.sql` -> (Anuka: `05_views.sql`, `06_queries.sql`) -> (Tanya: `07_roles.sql`)

(Name clash: Anuka's views file is also numbered 05. Rename the importer's output with
`--out 04b_real_import.sql` if you want strict ordering.)

## 5. What is real and what is not (say this in the report)
| Data | Status |
|---|---|
| antibiotic names/classes | real |
| 7 mutations + their drug associations | checked against published sources (see below) |
| 20 other mutations/associations | well-known mechanisms, **UNVERIFIED** (flagged in `evidence_source`) |
| real strains + AST results (`data_source = BV-BRC`) | real public data, imported by script |
| hospitals, treatments, outcomes, synthetic strains | **synthetic demo data** (no public patient-level source) |

Limits of the imported real data: `test_date` is set to the collection date (the source has
no AST date); `hospital_id` is NULL; real strains have no treatments/outcomes/mutation links.
They feed the lab-only resistance analysis (`resistance_phenotype`), which your report
already positions as independent of treatment.

## 6. References to add to the report
- Olson RD, et al. (2023). Introducing the Bacterial and Viral Bioinformatics Resource Center
  (BV-BRC). Nucleic Acids Research 51(D1):D678-D689. https://doi.org/10.1093/nar/gkac1003
  (already your reference [5])
- Antonopoulos DA, et al. (2019). PATRIC as a unique resource for studying antimicrobial
  resistance. Briefings in Bioinformatics 20(4):1094-1102. https://doi.org/10.1093/bib/bbx083
- VanOeffelen M, et al. (2021). A genomic data resource for predicting antimicrobial
  resistance from laboratory-derived antimicrobial susceptibility phenotypes. Briefings in
  Bioinformatics 22(6). (AMR file location: ftp.bvbrc.org/RELEASE_NOTES/PATRIC_genomes_AMR.txt)
- World Health Organization. Catalogue of mutations in Mycobacterium tuberculosis complex and
  their association with drug resistance. 1st ed. 2021 (WHO publication 9789240028173);
  2nd ed. 2023 (9789240082410). Also: Walker TM, et al. (2022) The 2021 WHO catalogue of
  M. tuberculosis complex mutations associated with drug resistance: a genotypic analysis.
  Lancet Microbe, doi 10.1016/S2666-5247(21)00301-3.
- E. coli gyrA S83L / D87N and parC S80I (fluoroquinolone resistance): PMC5702334
  (ST1193 clone study) and PMC1951223 (parE mutation in ESBL-producing E. coli,
  Antimicrob Agents Chemother). Open each PMC page and copy the full citation.
- mgrB inactivation and colistin resistance in K. pneumoniae: "The mgrB gene as a key target
  for acquired resistance to colistin in Klebsiella pneumoniae", J Antimicrob Chemother, vol 70;
  also PMC6194868 (India report). Confirm authors/pages on the journal page before citing.

Always open each source yourself and confirm title/authors/pages before it goes into the
final report. Citations above were located by search, not copied from a reference manager.

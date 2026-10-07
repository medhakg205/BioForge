#!/usr/bin/env python3
"""
BioForge seed generator (owner: Medha)

Usage:   python3 generate_seed.py          -> writes 04_seed.sql
Needs:   Python 3.8+, no external packages.

DATA PROVENANCE
  Reference tables (antibiotic, mutation, mutation_antibiotic_assoc):
    real gene/drug names. 7 mutations are checked against published
    sources (see VERIFIED below; citation stored in evidence_source);
    the rest are flagged UNVERIFIED in evidence_source.
  Patient-level tables (hospital, strain, strain_mutation, treatment,
    outcome, resistance_phenotype): SYNTHETIC. Linked strain-treatment-
    outcome records are not publicly available (patient privacy), which
    is the gap BioForge addresses.
Deterministic (fixed random seed) so the team gets identical data.

Planted patterns (so the analytics show something meaningful):
  1. Strains carrying a mutation linked to an antibiotic fail that
     antibiotic far more often (~65% vs ~10%).
  2. Resistance-mutation carriage rises every year 2021 -> 2025.
  3. Failures are mostly confirmed as resistance (resistance_confirmed).
"""
import json
import random
from datetime import date, timedelta

random.seed(2163)

N_STRAINS = 500
DATA_START = date(2021, 1, 1)
DATA_END = date(2025, 12, 31)
OUT_FILE = "04_seed.sql"

# --------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------
HOSPITALS = [  # fictional hospitals
    ("Riverside General Hospital", "Chennai", "India"),
    ("Lakeside Medical Centre", "Bengaluru", "India"),
    ("St. Mary's Teaching Hospital", "Hyderabad", "India"),
    ("Harbour City Hospital", "Colombo", "Sri Lanka"),
    ("Delta Regional Hospital", "Dhaka", "Bangladesh"),
]

# name, class, route, typical dose (mg)
ANTIBIOTICS = [
    ("Ciprofloxacin", "Fluoroquinolone", "oral", 500),
    ("Levofloxacin", "Fluoroquinolone", "oral", 750),
    ("Rifampicin", "Rifamycin", "oral", 600),
    ("Isoniazid", "Isonicotinic acid hydrazide", "oral", 300),
    ("Ampicillin", "Penicillin", "IV", 1000),
    ("Amoxicillin", "Penicillin", "oral", 500),
    ("Ceftriaxone", "Cephalosporin", "IV", 1000),
    ("Cefotaxime", "Cephalosporin", "IV", 1000),
    ("Meropenem", "Carbapenem", "IV", 1000),
    ("Imipenem", "Carbapenem", "IV", 500),
    ("Gentamicin", "Aminoglycoside", "IV", 240),
    ("Amikacin", "Aminoglycoside", "IV", 1000),
    ("Tetracycline", "Tetracycline", "oral", 500),
    ("Doxycycline", "Tetracycline", "oral", 100),
    ("Azithromycin", "Macrolide", "oral", 500),
    ("Erythromycin", "Macrolide", "oral", 500),
    ("Vancomycin", "Glycopeptide", "IV", 1000),
    ("Colistin", "Polymyxin", "IV", 300),
    ("Trimethoprim-Sulfamethoxazole", "Sulfonamide", "oral", 960),
    ("Linezolid", "Oxazolidinone", "oral", 600),
]
DOSE = {a[0]: a[3] for a in ANTIBIOTICS}

GN = ["Ciprofloxacin", "Levofloxacin", "Ampicillin", "Amoxicillin",
      "Ceftriaxone", "Cefotaxime", "Meropenem", "Imipenem", "Gentamicin",
      "Amikacin", "Tetracycline", "Doxycycline",
      "Trimethoprim-Sulfamethoxazole"]

# species -> (weight, drug panel)
SPECIES = {
    "Escherichia coli": (0.25, GN),
    "Klebsiella pneumoniae": (0.20, GN + ["Colistin"]),
    "Staphylococcus aureus": (0.15, ["Vancomycin", "Linezolid", "Erythromycin",
        "Azithromycin", "Doxycycline", "Tetracycline",
        "Trimethoprim-Sulfamethoxazole", "Ampicillin", "Amoxicillin",
        "Ceftriaxone", "Gentamicin"]),
    "Pseudomonas aeruginosa": (0.10, ["Ciprofloxacin", "Levofloxacin",
        "Meropenem", "Imipenem", "Gentamicin", "Amikacin", "Colistin"]),
    "Acinetobacter baumannii": (0.08, ["Meropenem", "Imipenem", "Colistin",
        "Amikacin", "Gentamicin", "Doxycycline", "Tetracycline",
        "Trimethoprim-Sulfamethoxazole"]),
    "Mycobacterium tuberculosis": (0.08, ["Rifampicin", "Isoniazid",
        "Levofloxacin", "Amikacin", "Linezolid"]),
    "Enterococcus faecium": (0.07, ["Vancomycin", "Linezolid", "Ampicillin",
        "Amoxicillin", "Gentamicin", "Tetracycline", "Doxycycline"]),
    "Streptococcus pneumoniae": (0.07, ["Ampicillin", "Amoxicillin",
        "Ceftriaxone", "Cefotaxime", "Erythromycin", "Azithromycin",
        "Levofloxacin", "Doxycycline", "Trimethoprim-Sulfamethoxazole",
        "Vancomycin"]),
}
SOURCES = ["blood", "urine", "sputum", "wound swab", "CSF", "respiratory aspirate"]

ENT = ["Escherichia coli", "Klebsiella pneumoniae"]
GRAM_NEG = ENT + ["Pseudomonas aeruginosa", "Acinetobacter baumannii"]
GRAM_POS = ["Staphylococcus aureus", "Enterococcus faecium",
            "Streptococcus pneumoniae"]
TB = ["Mycobacterium tuberculosis"]

# --------------------------------------------------------------------
# Curated mutations (real gene/drug pairs; coordinates are synthetic)
# key: (gene, type, pos, ref, alt, description, species, drugs, base_prob, effect)
# --------------------------------------------------------------------
CUR = [
    ("gyrA", "SNP", 248, "C", "T", "gyrA S83L (QRDR)", ["Escherichia coli"],
     ["Ciprofloxacin", "Levofloxacin"], 0.12, "resistance"),
    ("gyrA", "SNP", 259, "G", "A", "gyrA D87N (QRDR)", ["Escherichia coli"],
     ["Ciprofloxacin", "Levofloxacin"], 0.08, "resistance"),
    ("parC", "SNP", 239, "G", "T", "parC S80I (QRDR)", ["Escherichia coli"],
     ["Ciprofloxacin", "Levofloxacin"], 0.07, "resistance"),
    ("acrR", "frameshift", 112, "G", "GA", "acrR loss of function, efflux up-regulation", ENT,
     ["Ciprofloxacin"], 0.05, "reduced_susceptibility"),
    ("rpoB", "SNP", 1349, "C", "T", "rpoB S450L", TB, ["Rifampicin"], 0.10, "resistance"),
    ("rpoB", "SNP", 1333, "C", "T", "rpoB H445Y", TB, ["Rifampicin"], 0.05, "resistance"),
    ("katG", "SNP", 944, "G", "C", "katG S315T", TB, ["Isoniazid"], 0.12, "resistance"),
    ("blaCTX-M-15", "insertion", 5120, "-", "ISEcp1-blaCTX-M-15",
     "ESBL gene acquisition", ENT,
     ["Ceftriaxone", "Cefotaxime", "Ampicillin", "Amoxicillin"], 0.12, "resistance"),
    ("ampC", "SNP", 42, "C", "T", "ampC promoter -42C>T (hyperproduction)",
     ["Escherichia coli"], ["Ampicillin", "Amoxicillin"], 0.08, "resistance"),
    ("ompK36", "deletion", 330, "GATGAC", "-", "ompK36 loop 3 deletion",
     ["Klebsiella pneumoniae"], ["Meropenem", "Imipenem"], 0.06, "reduced_susceptibility"),
    ("ompK36", "frameshift", 215, "T", "TA", "ompK36 truncation",
     ["Klebsiella pneumoniae"], ["Meropenem"], 0.04, "resistance"),
    ("blaKPC-2", "insertion", 7010, "-", "Tn4401-blaKPC-2", "Carbapenemase acquisition",
     ENT + ["Pseudomonas aeruginosa"], ["Meropenem", "Imipenem"], 0.08, "resistance"),
    ("oprD", "frameshift", 760, "G", "GC", "oprD porin loss",
     ["Pseudomonas aeruginosa", "Acinetobacter baumannii"],
     ["Meropenem", "Imipenem"], 0.08, "resistance"),
    ("mgrB", "insertion", 88, "-", "IS5", "mgrB inactivation",
     ["Klebsiella pneumoniae"], ["Colistin"], 0.08, "resistance"),
    ("pmrB", "SNP", 359, "T", "C", "pmrB substitution",
     ["Pseudomonas aeruginosa", "Acinetobacter baumannii", "Klebsiella pneumoniae"],
     ["Colistin"], 0.05, "resistance"),
    ("rrs", "SNP", 1408, "A", "G", "16S rRNA A1408G", GRAM_NEG,
     ["Amikacin", "Gentamicin"], 0.04, "resistance"),
    ("tetA", "duplication", 1200, "TTCGA", "TTCGATTCGA", "tetA efflux gene duplication",
     ["Escherichia coli", "Klebsiella pneumoniae", "Acinetobacter baumannii"],
     ["Tetracycline", "Doxycycline"], 0.08, "resistance"),
    ("tetM", "insertion", 300, "-", "Tn916", "tetM ribosomal protection",
     GRAM_POS, ["Tetracycline", "Doxycycline"], 0.10, "resistance"),
    ("23S_rRNA", "SNP", 2059, "A", "G", "23S rRNA A2059G", GRAM_POS,
     ["Azithromycin", "Erythromycin"], 0.10, "resistance"),
    ("ermB", "insertion", 410, "-", "erm(B)-cassette", "ermB methylase",
     ["Staphylococcus aureus", "Streptococcus pneumoniae"],
     ["Erythromycin", "Azithromycin"], 0.08, "resistance"),
    ("vanA", "insertion", 9000, "-", "Tn1546-vanA", "vanA operon acquisition",
     ["Enterococcus faecium"], ["Vancomycin"], 0.15, "resistance"),
    ("dfrA", "SNP", 298, "A", "C", "dfrA substitution",
     ENT + ["Staphylococcus aureus", "Streptococcus pneumoniae"],
     ["Trimethoprim-Sulfamethoxazole"], 0.10, "resistance"),
    ("sul1", "insertion", 150, "-", "sul1-class1-integron", "sul1 on class 1 integron",
     GRAM_NEG, ["Trimethoprim-Sulfamethoxazole"], 0.08, "resistance"),
    ("rplC", "SNP", 463, "G", "C", "rplC G155R", ["Staphylococcus aureus", "Enterococcus faecium"],
     ["Linezolid"], 0.05, "resistance"),
    ("cfr", "insertion", 20, "-", "cfr-plasmid", "cfr rRNA methyltransferase",
     ["Staphylococcus aureus"], ["Linezolid"], 0.04, "resistance"),
    ("mecA", "insertion", 100, "-", "SCCmec-mecA", "PBP2a acquisition",
     ["Staphylococcus aureus"],
     ["Ampicillin", "Amoxicillin", "Ceftriaxone"], 0.20, "resistance"),
    ("pbp2x", "SNP", 1100, "T", "C", "pbp2x altered penicillin-binding protein",
     ["Streptococcus pneumoniae"],
     ["Ampicillin", "Amoxicillin", "Ceftriaxone"], 0.10, "resistance"),
]


# --------------------------------------------------------------------
# PROVENANCE. Only entries listed here were checked against published
# sources. For these, coordinates are protein-level (amino-acid residue
# number, one-letter codes) and the source is stored in evidence_source.
# Everything else in CUR is a well-known mechanism that has NOT been
# checked in this project yet: genome_position is set to NULL and
# evidence_source says UNVERIFIED. Replace/confirm before citing.
# key = (gene, description) -> (position, ref, alt, source)
# --------------------------------------------------------------------
SRC_FQ = ("Verified: QRDR substitutions in fluoroquinolone-resistant E. coli "
          "(PMC5702334; PMC1951223)")
SRC_TB = ("Verified: WHO Catalogue of mutations in M. tuberculosis complex "
          "(1st ed. 2021, WHO pub 9789240028173; 2nd ed. 2023, 9789240082410)")
SRC_MGRB = ("Verified: mgrB insertional inactivation -> colistin resistance in "
            "K. pneumoniae (J Antimicrob Chemother vol 70; PMC6194868)")
SRC_UNVERIFIED = ("UNVERIFIED: well-known mechanism, citation to be added "
                  "(check CARD / literature) before use")
VERIFIED = {
    ("gyrA", "gyrA S83L (QRDR)"): (83, "S", "L", SRC_FQ),
    ("gyrA", "gyrA D87N (QRDR)"): (87, "D", "N", SRC_FQ),
    ("parC", "parC S80I (QRDR)"): (80, "S", "I", SRC_FQ),
    ("rpoB", "rpoB S450L"): (450, "S", "L", SRC_TB),
    ("rpoB", "rpoB H445Y"): (445, "H", "Y", SRC_TB),
    ("katG", "katG S315T"): (315, "S", "T", SRC_TB),
    ("mgrB", "mgrB inactivation"): (None, "-", "IS5-like", SRC_MGRB),
}

FILLER_GENES = ["recA", "dnaK", "rpoD", "gyrB", "lacZ", "murA", "ftsZ", "fabI",
                "hns", "rpsA", "tufA", "infB", "glnA", "sodB", "katE", "ompA",
                "fliC", "pilA", "lptD", "bamA", "secY", "atpD", "pykF", "gltA"]
N_FILLERS = 0   # fabricated background variants removed (not real data)

SEQ_METHODS = ["WGS-Illumina", "WGS-Nanopore", "Sanger", "Targeted PCR panel"]
PLATFORMS = ["Illumina NovaSeq", "Illumina MiSeq", "Oxford Nanopore MinION",
             "PacBio Sequel II"]
PLASMIDS = ["IncFII", "IncN", "IncX3", "ColE1", "IncHI2", "IncL/M"]
PHYSICIANS = ["Dr. A. Kumar", "Dr. S. Iyer", "Dr. R. Menon", "Dr. P. Nair",
              "Dr. L. Fernando", "Dr. M. Rahman", "Dr. K. Reddy", "Dr. V. Shah"]
FAIL_NOTES = ["Switched to alternative agent", "Resistance detected on repeat culture",
              "Escalated to combination therapy", "Referred to infectious disease unit"]


# --------------------------------------------------------------------
# SQL helpers
# --------------------------------------------------------------------
def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, date):
        return "'%s'" % v.isoformat()
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return "'%s'" % s


def insert(out, table, cols, rows, batch=200):
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        out.append("INSERT INTO %s (%s) VALUES" % (table, ", ".join(cols)))
        out.append(",\n".join("  (" + ", ".join(lit(x) for x in r) + ")" for r in chunk) + ";")
        out.append("")


def rand_date(a, b):
    return a + timedelta(days=random.randint(0, (b - a).days))


# --------------------------------------------------------------------
# Build data
# --------------------------------------------------------------------
def main():
    antibiotic_id = {a[0]: i + 1 for i, a in enumerate(ANTIBIOTICS)}

    # ---- mutations ----
    mutations = []   # dicts
    sigs = set()
    for (gene, mtype, pos, ref, alt, desc, sp, drugs, p, eff) in CUR:
        v = VERIFIED.get((gene, desc))
        if v:
            pos, ref, alt, src = v
            if pos is not None:
                desc = desc + " [amino-acid residue numbering]"
        else:
            pos, src = None, SRC_UNVERIFIED     # do not claim coordinates
        sigs.add((gene, pos, ref, alt))
        mutations.append(dict(gene=gene, type=mtype, pos=pos, ref=ref, alt=alt,
                              desc=desc, species=sp, drugs=drugs, p=p,
                              effect=eff, curated=True, source=src))

    dna = "ACGT"
    types = ["SNP", "insertion", "deletion", "frameshift", "duplication", "inversion"]
    while sum(1 for m in mutations if not m["curated"]) < N_FILLERS:
        gene = random.choice(FILLER_GENES)
        mtype = random.choice(types)
        pos = random.randint(100, 4_500_000)
        if mtype == "SNP":
            ref = random.choice(dna)
            alt = random.choice([b for b in dna if b != ref])
        elif mtype == "insertion":
            ref, alt = "-", "".join(random.choices(dna, k=random.randint(1, 6)))
        elif mtype == "deletion":
            ref, alt = "".join(random.choices(dna, k=random.randint(1, 6))), "-"
        elif mtype == "frameshift":
            ref = random.choice(dna)
            alt = ref + random.choice(dna)
        elif mtype == "duplication":
            ref = "".join(random.choices(dna, k=random.randint(2, 5)))
            alt = ref + ref
        else:  # inversion
            while True:
                ref = "".join(random.choices(dna, k=random.randint(4, 6)))
                alt = ref[::-1]
                if alt != ref:
                    break
        if (gene, pos, ref, alt) in sigs:
            continue
        sigs.add((gene, pos, ref, alt))
        mutations.append(dict(gene=gene, type=mtype, pos=pos, ref=ref, alt=alt,
                              desc="Background variant (no known drug association)",
                              species=None, drugs=[], p=0.04, effect=None,
                              curated=False))
    for i, m in enumerate(mutations, start=1):
        m["id"] = i
    curated = [m for m in mutations if m["curated"]]
    fillers = [m for m in mutations if not m["curated"]]

    # ---- strains + strain_mutations ----
    sp_names = list(SPECIES)
    sp_weights = [SPECIES[s][0] for s in sp_names]
    strains, strain_muts, strain_info = [], [], {}
    for sid in range(1, N_STRAINS + 1):
        species = random.choices(sp_names, sp_weights)[0]
        hosp = random.randint(1, len(HOSPITALS))
        h = HOSPITALS[hosp - 1]
        coll = rand_date(DATA_START, DATA_END)
        year_factor = 1 + 0.35 * (coll.year - DATA_START.year)   # rising trend

        chosen = []
        for m in curated:
            if species in m["species"] and random.random() < min(0.9, m["p"] * year_factor):
                chosen.append(m)
        for m in fillers:
            if random.random() < 0.025:
                chosen.append(m)
        random.shuffle(chosen)
        chosen = chosen[:5]

        meta = {"data_source": "synthetic", "platform": random.choice(PLATFORMS),
                "coverage_x": random.randint(30, 150),
                "assembly_n50": random.randint(50_000, 5_000_000),
                "plasmids": random.sample(PLASMIDS, random.randint(0, 3))}
        if random.random() < 0.4:
            meta["read_length"] = random.choice([100, 150, 250])
        if random.random() < 0.2:
            meta["contamination_pct"] = round(random.uniform(0, 3), 2)

        source = "sputum" if species in TB else random.choice(SOURCES)
        strains.append((sid, hosp, species, source, coll,
                        "%s, %s" % (h[1], h[2]), "BF-ACC-%06d" % sid,
                        json.dumps(meta)))
        for m in chosen:
            strain_muts.append((sid, m["id"],
                                coll + timedelta(days=random.randint(1, 30)),
                                random.choice(SEQ_METHODS),
                                round(random.uniform(0.70, 1.00), 2)))
        strain_info[sid] = dict(species=species, coll=coll, muts=chosen)

    # ---- treatments + outcomes ----
    treatments, outcomes = [], []
    tid = 0
    for sid, info in strain_info.items():
        panel = SPECIES[info["species"]][1]
        n = min(random.randint(1, 5), len(panel))
        for drug in random.sample(panel, n):
            tid += 1
            start = min(info["coll"] + timedelta(days=random.randint(0, 14)), DATA_END)
            is_tb = info["species"] in TB
            dur = random.randint(90, 180) if is_tb else random.randint(5, 21)
            treatments.append((tid, sid, antibiotic_id[drug], float(DOSE[drug]),
                               dur, start, random.choice(PHYSICIANS)))

            resistant = any(drug in m["drugs"] for m in info["muts"])
            fail_p = 0.65 if resistant else 0.10
            if random.random() < 0.03:
                result = "ongoing"
            elif random.random() < fail_p:
                result = random.choices(["failed", "relapsed", "deceased"],
                                        [0.60, 0.25, 0.15])[0]
            else:
                result = "cured"
            bad = result in ("failed", "relapsed", "deceased")
            if resistant and bad:
                conf = random.random() < 0.85
            elif resistant:
                conf = random.random() < 0.15
            else:
                conf = random.random() < 0.03
            follow = None if result == "ongoing" else \
                start + timedelta(days=dur + random.randint(0, 30))
            note = random.choice(FAIL_NOTES) if bad and random.random() < 0.5 else None
            outcomes.append((tid, result, conf, follow, note))
            info.setdefault("drug_resistant", {})[drug] = resistant

    # ---- resistance phenotypes (lab-only) ----
    phenos = []
    for sid, info in strain_info.items():
        panel = SPECIES[info["species"]][1]
        for drug in random.sample(panel, min(random.randint(0, 3), len(panel))):
            resistant = any(drug in m["drugs"] for m in info["muts"])
            if resistant:
                s = random.choices(["R", "I", "S"], [0.90, 0.08, 0.02])[0]
            else:
                s = random.choices(["S", "I", "R"], [0.88, 0.08, 0.04])[0]
            mic = {"R": random.choice([8, 16, 32, 64, 128]),
                   "I": random.choice([2, 4]),
                   "S": random.choice([0.06, 0.125, 0.25, 0.5, 1])}[s]
            phenos.append((sid, antibiotic_id[drug], float(mic), s,
                           random.choice(["MIC", "disk_diffusion", "E-test", "automated"]),
                           info["coll"] + timedelta(days=random.randint(1, 10))))

    # ---- literature associations ----
    assocs = []
    for m in curated:
        for drug in m["drugs"]:
            assocs.append((m["id"], antibiotic_id[drug], m["effect"], m["source"]))

    # ---- write SQL ----
    out = ["-- BioForge 04_seed.sql  (GENERATED by generate_seed.py - synthetic data)",
           "-- Run AFTER 01_schema.sql (and after 02/03 if present).",
           "USE bioforge;", "SET FOREIGN_KEY_CHECKS = 0;", ""]
    insert(out, "hospital", ["hospital_id", "name", "city", "country"],
           [(i + 1,) + h for i, h in enumerate(HOSPITALS)])
    insert(out, "antibiotic", ["antibiotic_id", "name", "drug_class", "route"],
           [(i + 1, a[0], a[1], a[2]) for i, a in enumerate(ANTIBIOTICS)])
    insert(out, "mutation",
           ["mutation_id", "gene_name", "mutation_type", "genome_position",
            "ref_allele", "alt_allele", "description"],
           [(m["id"], m["gene"], m["type"], m["pos"], m["ref"], m["alt"], m["desc"])
            for m in mutations])
    insert(out, "strain",
           ["strain_id", "hospital_id", "species", "isolate_source", "collection_date",
            "geographic_origin", "genome_accession", "genomic_metadata"], strains)
    insert(out, "strain_mutation",
           ["strain_id", "mutation_id", "detection_date", "sequencing_method",
            "confidence_score"], strain_muts)
    insert(out, "treatment",
           ["treatment_id", "strain_id", "antibiotic_id", "dosage_mg", "duration_days",
            "start_date", "prescribing_physician"], treatments)
    insert(out, "outcome",
           ["treatment_id", "result", "resistance_confirmed", "follow_up_date", "notes"],
           outcomes)
    insert(out, "resistance_phenotype",
           ["strain_id", "antibiotic_id", "mic_value", "susceptibility",
            "test_method", "test_date"], phenos)
    insert(out, "mutation_antibiotic_assoc",
           ["mutation_id", "antibiotic_id", "effect", "evidence_source"], assocs)
    out += ["SET FOREIGN_KEY_CHECKS = 1;", ""]

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("Wrote", OUT_FILE)
    print("hospital:", len(HOSPITALS), "| antibiotic:", len(ANTIBIOTICS),
          "| mutation:", len(mutations), "| strain:", len(strains))
    print("strain_mutation:", len(strain_muts), "| treatment:", len(treatments),
          "| outcome:", len(outcomes), "| phenotype:", len(phenos),
          "| assoc:", len(assocs))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
BioForge real-data importer (owner: Medha)

Turns REAL public data from BV-BRC (Bacterial and Viral Bioinformatics
Resource Center) into SQL for the BioForge `strain` and
`resistance_phenotype` tables.

Inputs (you download these yourself, see README.md):
  --amr     one or more BV-BRC AMR phenotype files: either the FTP file
            PATRIC_genomes_AMR.txt, or CSV downloads of the "AMR Phenotypes"
            tab on bv-brc.org (one per species is fine). Columns include
            genome id, genome name, antibiotic, resistant phenotype,
            measurement value/unit, laboratory typing method.
  --genomes one or more BV-BRC genome tables (CSV/TSV downloaded from the
            "Genomes" tab, or the FTP genome_metadata file) that include
            Genome ID, Genome Name, Collection Date, Isolation Country,
            Isolation Source, Assembly Accession. Column names are matched
            loosely (case/space/underscore-insensitive).

Output:
  05_real_import.sql   -> run AFTER 01_schema.sql and 04_seed.sql

What is real vs. assumed (also stored in strain.genomic_metadata JSON):
  REAL     : species, isolation source, country, collection date, accession,
             antibiotic, S/I/R call, MIC value, lab typing method.
  ASSUMED  : test_date is not in the source, so it is set to the strain's
             collection date. hospital_id is NULL (source has no hospital).
  ABSENT   : no treatments/outcomes/mutation links are created for real
             strains (not available in public data).

Usage:
  python3 import_real_strains.py --amr ecoli_amr.csv kpn_amr.csv \
      --genomes ecoli_genomes.csv kpn_genomes.csv --per-species 60
Needs Python 3.8+, no external packages.
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import date

csv.field_size_limit(10**7)
random.seed(2163)

ID_OFFSET = 100000          # real strains get ids 100001+ (synthetic use 1-500)

BIOFORGE_SPECIES = [
    "Escherichia coli", "Klebsiella pneumoniae", "Staphylococcus aureus",
    "Pseudomonas aeruginosa", "Acinetobacter baumannii",
    "Mycobacterium tuberculosis", "Enterococcus faecium",
    "Streptococcus pneumoniae",
]

# BV-BRC antibiotic name (lowercase) -> antibiotic_id in 04_seed.sql
ANTIBIOTIC_IDS = {
    "ciprofloxacin": 1, "levofloxacin": 2, "rifampicin": 3, "rifampin": 3,
    "isoniazid": 4, "ampicillin": 5, "amoxicillin": 6, "ceftriaxone": 7,
    "cefotaxime": 8, "meropenem": 9, "imipenem": 10, "gentamicin": 11,
    "amikacin": 12, "tetracycline": 13, "doxycycline": 14,
    "azithromycin": 15, "erythromycin": 16, "vancomycin": 17,
    "colistin": 18, "trimethoprim-sulfamethoxazole": 19,
    "trimethoprim/sulfamethoxazole": 19, "sulfamethoxazole/trimethoprim": 19,
    "sulfamethoxazole-trimethoprim": 19, "co-trimoxazole": 19,
    "linezolid": 20,
}

ALIASES = {
    # AMR file
    "genome_id": ["genomeid"], "genome_name": ["genomename"],
    "antibiotic": ["antibiotic"], "phenotype": ["resistantphenotype"],
    "mvalue": ["measurementvalue"], "munit": ["measurementunit"],
    "method": ["laboratorytypingmethod"],
    # genome file
    "g_id": ["genomeid"], "g_name": ["genomename"],
    "g_date": ["collectiondate"],
    "g_country": ["isolationcountry", "geographiclocation"],
    "g_source": ["isolationsource"],
    "g_acc": ["assemblyaccession", "genbankaccessions"],
}


def norm(h):
    return re.sub(r"[^a-z0-9]", "", h.lower())


def read_table(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        head = f.readline()
        f.seek(0)
        delim = "\t" if head.count("\t") >= head.count(",") else ","
        rdr = csv.reader(f, delimiter=delim)
        headers = next(rdr)
        rows = [r for r in rdr if r]
    return headers, rows


def col(headers, keys):
    nh = [norm(h) for h in headers]
    for k in ALIASES[keys]:
        if k in nh:
            return nh.index(k)
    return None


def need(headers, keys, label, path):
    i = col(headers, keys)
    if i is None:
        sys.exit("ERROR: could not find a '%s' column in %s.\n"
                 "Columns found: %s" % (label, path, headers))
    return i


def parse_date(s):
    m = re.match(r"^\s*(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", s or "")
    if not m:
        return None, None
    y = int(m.group(1))
    if y < 1900 or y > date.today().year:
        return None, None
    mo, d = m.group(2), m.group(3)
    try:
        if d:
            return date(y, int(mo), int(d)), "day"
        if mo:
            return date(y, int(mo), 1), "month"
        return date(y, 1, 1), "year"
    except ValueError:
        return None, None


def species_of(name):
    for sp in BIOFORGE_SPECIES:
        if name.lower().startswith(sp.lower()):
            return sp
    return None


def map_method(m):
    m = (m or "").lower()
    if "disk" in m or "disc" in m:
        return "disk_diffusion"
    if "e-test" in m or "etest" in m:
        return "E-test"
    if any(k in m for k in ("vitek", "phoenix", "microscan", "automat", "sensititre")):
        return "automated"
    return "MIC"


def map_phenotype(p):
    p = (p or "").strip().lower()
    if p == "resistant":
        return "R"
    if p == "susceptible":
        return "S"
    if p in ("intermediate", "susceptible-dose dependent", "susceptible dose-dependent"):
        return "I"
    return None


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, date):
        return "'%s'" % v.isoformat()
    return "'%s'" % str(v).replace("\\", "\\\\").replace("'", "''")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amr", required=True, nargs="+")
    ap.add_argument("--genomes", required=True, nargs="+")
    ap.add_argument("--out", default="05_real_import.sql")
    ap.add_argument("--per-species", type=int, default=60,
                    help="max strains imported per species (default 60)")
    a = ap.parse_args()

    # ---- genome metadata (one or more files) ----
    genomes = {}
    for path in a.genomes:
        gh, grows = read_table(path)
        gi = dict(id=need(gh, "g_id", "Genome ID", path),
                  name=need(gh, "g_name", "Genome Name", path),
                  date=need(gh, "g_date", "Collection Date", path),
                  country=col(gh, "g_country"), source=col(gh, "g_source"),
                  acc=col(gh, "g_acc"))

        def gcell(r, k):
            i = gi[k]
            return r[i].strip() if i is not None and i < len(r) else ""
        for r in grows:
            gid = gcell(r, "id")
            if gid:
                genomes[gid] = {k: gcell(r, k) for k in
                                ("name", "date", "country", "source", "acc")}

    # ---- AMR phenotypes (one or more files) ----
    stats = Counter()
    per_genome = defaultdict(list)
    for path in a.amr:
        ah, arows = read_table(path)
        ai = dict(id=need(ah, "genome_id", "genome id", path),
                  abx=need(ah, "antibiotic", "antibiotic", path),
                  pheno=need(ah, "phenotype", "resistant phenotype", path),
                  mval=col(ah, "mvalue"), munit=col(ah, "munit"),
                  method=col(ah, "method"))

        def cell(r, i):
            return r[i].strip() if i is not None and i < len(r) else ""
        for r in arows:
            stats["amr_rows"] += 1
            gid = cell(r, ai["id"])
            abx = ANTIBIOTIC_IDS.get(cell(r, ai["abx"]).lower())
            ph = map_phenotype(cell(r, ai["pheno"]))
            if abx is None:
                stats["skipped_antibiotic_not_in_bioforge"] += 1
                continue
            if ph is None:
                stats["skipped_unusable_phenotype"] += 1
                continue
            if gid not in genomes:
                stats["skipped_no_genome_metadata"] += 1
                continue
            per_genome[gid].append((abx, ph, cell(r, ai["mval"]),
                                    cell(r, ai["munit"]), cell(r, ai["method"])))

    # ---- choose strains ----
    by_species = defaultdict(list)
    for gid in per_genome:
        g = genomes[gid]
        sp = species_of(g["name"])
        if sp is None:
            stats["skipped_species_not_in_bioforge"] += 1
            continue
        d, prec = parse_date(g["date"])
        if d is None:
            stats["skipped_no_valid_collection_date"] += 1
            continue
        by_species[sp].append(gid)

    chosen = []
    for sp in BIOFORGE_SPECIES:
        ids = sorted(by_species[sp])
        random.shuffle(ids)
        chosen += [(sp, g) for g in ids[:a.per_species]]

    # ---- build rows ----
    strains, phenos, used_acc = [], [], set()
    for n, (sp, gid) in enumerate(chosen, start=1):
        g = genomes[gid]
        sid = ID_OFFSET + n
        d, prec = parse_date(g["date"])
        acc = re.split(r"[,;\s]+", g["acc"])[0] if g["acc"] else ""
        if not acc or len(acc) > 50 or acc in used_acc:
            acc = "BVBRC-" + gid
        used_acc.add(acc)
        methods = sorted({map_method(p[4]) for p in per_genome[gid]})
        meta = {"data_source": "BV-BRC", "bvbrc_genome_id": gid,
                "collection_date_precision": prec,
                "test_date_note": "AST date not provided by source; set to collection date",
                "ast_methods": methods}
        strains.append((sid, None, sp, g["source"] or None, d,
                        g["country"] or None, acc, json.dumps(meta)))
        for abx, ph, mv, mu, meth in per_genome[gid]:
            m = re.search(r"[-+]?\d*\.?\d+", mv or "")
            is_mm = "mm" in (mu or "").lower()
            tm = map_method(meth)
            mic = (float(m.group()) if (m and not is_mm and tm != "disk_diffusion"
                                        and float(m.group()) < 100000) else None)
            phenos.append((sid, abx, mic, ph, tm, d))

    # ---- write ----
    out = ["-- BioForge 05_real_import.sql  (GENERATED by import_real_strains.py)",
           "-- REAL strains + lab AST results from BV-BRC. Run AFTER 04_seed.sql.",
           "USE bioforge;", ""]

    def ins(table, cols, rows, ignore=False, batch=200):
        for i in range(0, len(rows), batch):
            out.append("INSERT %sINTO %s (%s) VALUES" %
                       ("IGNORE " if ignore else "", table, ", ".join(cols)))
            out.append(",\n".join("  (" + ", ".join(lit(x) for x in r) + ")"
                                  for r in rows[i:i + batch]) + ";")
            out.append("")

    ins("strain", ["strain_id", "hospital_id", "species", "isolate_source",
                   "collection_date", "geographic_origin", "genome_accession",
                   "genomic_metadata"], strains)
    ins("resistance_phenotype", ["strain_id", "antibiotic_id", "mic_value",
                                 "susceptibility", "test_method", "test_date"],
        phenos, ignore=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("Wrote %s" % a.out)
    print("strains imported:", len(strains), "| phenotype rows:", len(phenos))
    print("per species:", dict(Counter(s[2] for s in strains)))
    for k, v in sorted(stats.items()):
        print("  %-40s %d" % (k, v))
    if not strains:
        print("\nNo strains imported. Check that your genomes file has Collection "
              "Date filled in and that the Genome IDs match the AMR file.")


if __name__ == "__main__":
    main()
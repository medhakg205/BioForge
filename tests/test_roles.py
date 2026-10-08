from app.db import get_connection

# (role, description, SQL, should_succeed)
TESTS = [
    ("researcher", "read strain",                      "SELECT COUNT(*) FROM strain", True),
    ("researcher", "read de-identified treatments",    "SELECT COUNT(*) FROM v_treatment_deidentified", True),
    ("researcher", "read Anuka view: resistance rate",  "SELECT COUNT(*) FROM v_resistance_rate_monthly", True),
    ("researcher", "read Anuka view: mutation failure", "SELECT COUNT(*) FROM v_mutation_treatment_failure", True),
    ("researcher", "read prescribing_physician",       "SELECT prescribing_physician FROM treatment LIMIT 1", False),
    ("researcher", "update outcome",                   "UPDATE outcome SET notes='x' WHERE outcome_id=1", False),
    ("clinician",  "read treatment",                   "SELECT COUNT(*) FROM treatment", True),
    ("clinician",  "update outcome",                   "UPDATE outcome SET notes='x' WHERE outcome_id=1", True),
    ("clinician",  "update strain",                    "UPDATE strain SET species='x' WHERE strain_id=1", False),
    ("clinician",  "delete treatment",                 "DELETE FROM treatment WHERE treatment_id=1", False),
    ("etl",        "insert mutation",                  "INSERT INTO mutation (gene_name, mutation_type) VALUES ('testgene','SNP')", True),
    ("etl",        "read strain",                      "SELECT COUNT(*) FROM strain", False),
    ("etl",        "update outcome",                   "UPDATE outcome SET notes='x' WHERE outcome_id=1", False),
    ("admin",      "read treatment",                   "SELECT COUNT(*) FROM treatment", True),
    ("admin",      "update outcome",                   "UPDATE outcome SET notes='x' WHERE outcome_id=1", True),
]

conns = {}
print(f"{'ROLE':11} {'ACTION':36} {'EXPECTED':9} {'ACTUAL':9} RESULT")
for role, desc, sql, should in TESTS:
    if role not in conns:
        conns[role] = get_connection(role)
    conn = conns[role]
    try:
        cur = conn.cursor()
        cur.execute(sql)
        if cur.with_rows:
            cur.fetchall()
        actual = True
    except Exception:
        actual = False
    finally:
        conn.rollback()   # never keep test changes
    print(f"{role:11} {desc:36} {'allowed' if should else 'denied':9} "
          f"{'allowed' if actual else 'denied':9} {'PASS' if actual == should else 'FAIL'}")

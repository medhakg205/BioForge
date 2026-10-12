from datetime import date, timedelta

import mysql.connector
import pytest

from app.db import get_connection


# (role, description, SQL, should_succeed)
TESTS = [
    ("researcher", "read strain", "SELECT COUNT(*) FROM strain", True),
    ("researcher", "read de-identified treatments",
     "SELECT COUNT(*) FROM v_treatment_deidentified", True),
    ("researcher", "read resistance rate",
     "SELECT COUNT(*) FROM v_resistance_rate_monthly", True),
    ("researcher", "read mutation failure",
     "SELECT COUNT(*) FROM v_mutation_treatment_failure", True),
    ("researcher", "read prescribing physician",
     "SELECT prescribing_physician FROM treatment LIMIT 1", False),
    ("researcher", "read audit log",
     "SELECT COUNT(*) FROM audit_log", False),
    ("researcher", "update outcome",
     "UPDATE outcome SET notes='x' WHERE outcome_id=1", False),
    ("clinician", "read treatment",
     "SELECT COUNT(*) FROM treatment", True),
    ("clinician", "read audit log",
     "SELECT COUNT(*) FROM audit_log", False),
    ("clinician", "update outcome",
     "UPDATE outcome SET notes='x' WHERE outcome_id=1", True),
    ("clinician", "update strain",
     "UPDATE strain SET species='x' WHERE strain_id=1", False),
    ("clinician", "delete treatment",
     "DELETE FROM treatment WHERE treatment_id=1", False),
    ("etl", "insert mutation",
     "INSERT INTO mutation (gene_name, mutation_type) VALUES ('testgene','SNP')", True),
    ("etl", "read strain",
     "SELECT COUNT(*) FROM strain", False),
    ("etl", "update outcome",
     "UPDATE outcome SET notes='x' WHERE outcome_id=1", False),
    ("admin", "read treatment",
     "SELECT COUNT(*) FROM treatment", True),
    ("admin", "read audit log",
     "SELECT COUNT(*) FROM audit_log", True),
    ("admin", "insert audit log",
     """INSERT INTO audit_log
        (table_name, record_id, `action`, old_values, new_values, changed_by)
        VALUES ('test', 1, 'UPDATE', JSON_OBJECT(), JSON_OBJECT(), CURRENT_USER())""", True),
    ("admin", "update audit log",
     "UPDATE audit_log SET `action`='UPDATE' WHERE audit_id=0", True),
    ("admin", "delete audit log",
     "DELETE FROM audit_log WHERE audit_id=0", True),
    ("admin", "update outcome",
     "UPDATE outcome SET notes='x' WHERE outcome_id=1", True),
]


@pytest.mark.parametrize("role,description,sql,should_succeed", TESTS)
def test_role_permissions(role, description, sql, should_succeed):
    conn = get_connection(role)
    actual = False
    try:
        cur = conn.cursor()
        cur.execute(sql)
        if cur.with_rows:
            cur.fetchall()
        actual = True
    except mysql.connector.Error:
        actual = False
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()

    assert actual is should_succeed, (
        f"{role} permission check failed for {description}: "
        f"expected {'allowed' if should_succeed else 'denied'}"
    )


def test_clinician_can_execute_record_treatment_procedure():
    conn = get_connection("clinician")
    treatment_id = None
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT s.strain_id, a.antibiotic_id
               FROM strain s CROSS JOIN antibiotic a
               WHERE s.is_active = TRUE
               ORDER BY s.strain_id, a.antibiotic_id
               LIMIT 1"""
        )
        reference = cur.fetchone()
        if reference is None:
            pytest.skip("The integration database needs an active strain and antibiotic.")

        start_date = date.today()
        cur.execute(
            """CALL sp_record_treatment(
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
               )""",
            (reference[0], reference[1], 1.00, 1, start_date, "Role test",
             "cured", False, start_date + timedelta(days=1), None),
        )
        result = cur.fetchone()
        assert result is not None, "Procedure did not return the created treatment ID."
        treatment_id = result[0]
        while cur.nextset():
            cur.fetchall()
    finally:
        conn.close()
        if treatment_id is not None:
            admin = get_connection("admin")
            try:
                cur = admin.cursor()
                cur.execute("DELETE FROM outcome WHERE treatment_id = %s", (treatment_id,))
                cur.execute("DELETE FROM treatment WHERE treatment_id = %s", (treatment_id,))
                admin.commit()
            finally:
                admin.close()


def test_admin_has_full_database_access():
    conn = get_connection("admin")
    try:
        cur = conn.cursor()
        cur.execute("SHOW GRANTS")
        grants = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

    assert any("ALL PRIVILEGES ON `bioforge`.*" in grant for grant in grants)

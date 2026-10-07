import os
import mysql.connector

ROLES = ("clinician", "researcher", "admin", "etl")


def get_connection(role):
    """Return a mysql.connector connection logged in as the given role.

    Credentials come from environment variables (never from files):
      BIOFORGE_HOST (default localhost), BIOFORGE_PORT (default 3306),
      BIOFORGE_DB (default bioforge),
      BIOFORGE_<ROLE>_USER (default bioforge_<role>),
      BIOFORGE_<ROLE>_PASSWORD (required).
    """
    role = role.lower()
    if role not in ROLES:
        raise ValueError(f"Unknown role '{role}'. Use one of {ROLES}")

    prefix = f"BIOFORGE_{role.upper()}"
    password = os.environ.get(f"{prefix}_PASSWORD")
    if password is None:
        raise RuntimeError(f"Set the environment variable {prefix}_PASSWORD")

    return mysql.connector.connect(
        host=os.environ.get("BIOFORGE_HOST", "localhost"),
        port=int(os.environ.get("BIOFORGE_PORT", "3306")),
        database=os.environ.get("BIOFORGE_DB", "bioforge"),
        user=os.environ.get(f"{prefix}_USER", f"bioforge_{role}"),
        password=password,
    )

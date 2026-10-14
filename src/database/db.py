"""
db.py
-------------------------------------------------------------------------------
Handles the SQLite database connection and one-time initialization.

Beginner note: SQLite stores the whole database in a single file on disk
(see src/utils/config.py -> DATABASE_PATH). There is no separate database
server to install or run.
-------------------------------------------------------------------------------
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """
    Open a new connection to the SQLite database file.

    `row_factory = sqlite3.Row` lets query results be accessed like
    dictionaries (row["calories"]) instead of only by numeric index,
    which is much easier to read for beginners.
    """
    config.ensure_directories()
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit: bool = False):
    """
    A convenience context manager:

        with get_cursor(commit=True) as cur:
            cur.execute("INSERT INTO ...")

    It opens a connection, hands you a cursor, and closes the connection
    afterwards (committing first if commit=True). This avoids repeating
    connect/close boilerplate in every repository function.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    """
    Create all tables (if they do not already exist) by running schema.sql.
    Safe to call every time the app starts -- `CREATE TABLE IF NOT EXISTS`
    means it will not wipe existing data.
    """
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database schema is ready at %s", config.DATABASE_PATH)
    finally:
        conn.close()


def is_database_seeded() -> bool:
    """Return True if the foods table already has data."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM foods")
        row = cur.fetchone()
        return row["n"] > 0

import sqlite3
from collections.abc import Generator

DATABASE_PATH = "app.db"


def init_db() -> None:
    """Create tables if they don't exist yet."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                title             TEXT    NOT NULL,
                description       TEXT,
                original_filename TEXT    NOT NULL,
                stored_filename   TEXT    NOT NULL UNIQUE,
                content_type      TEXT    NOT NULL,
                size_bytes        INTEGER NOT NULL,
                created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            )
            """
        )


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: one connection per request, closed afterwards."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["title"]
    try:
        yield conn
    finally:
        conn.close()

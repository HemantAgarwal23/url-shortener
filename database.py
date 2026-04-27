import sqlite3
from contextlib import closing
from typing import Optional


DB_PATH = "url_shortener.db"


def init_db() -> None:
    """Create required tables and apply lightweight schema migrations."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url TEXT NOT NULL,
                short_code TEXT NOT NULL UNIQUE,
                click_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_click_count_column(conn)
        ensure_created_at_column(conn)
        conn.commit()


def _get_link_table_columns(conn: sqlite3.Connection) -> set[str]:
    """Return current column names for the links table."""
    with closing(conn.cursor()) as cursor:
        cursor.execute("PRAGMA table_info(links)")
        return {row[1] for row in cursor.fetchall()}


def ensure_click_count_column(conn: sqlite3.Connection) -> None:
    """Add click_count for databases created before this field existed."""
    columns = _get_link_table_columns(conn)
    with closing(conn.cursor()) as cursor:
        if "click_count" not in columns:
            cursor.execute(
                "ALTER TABLE links ADD COLUMN click_count INTEGER NOT NULL DEFAULT 0"
            )


def ensure_created_at_column(conn: sqlite3.Connection) -> None:
    """Add created_at for databases created before this field existed."""
    columns = _get_link_table_columns(conn)
    with closing(conn.cursor()) as cursor:
        if "created_at" not in columns:
            cursor.execute("ALTER TABLE links ADD COLUMN created_at TEXT")
            cursor.execute(
                "UPDATE links SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
            )


def short_code_exists(short_code: str) -> bool:
    """Return True if the given short code already exists."""
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT 1 FROM links WHERE short_code = ?", (short_code,))
            return cursor.fetchone() is not None


def get_existing_link_for_url(long_url: str) -> Optional[tuple[str, int, str]]:
    """Return existing short code, click count, and created_at for a URL."""
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "SELECT short_code, click_count, created_at FROM links WHERE long_url = ?",
                (long_url,),
            )
            row = cursor.fetchone()
            return (row[0], row[1], row[2]) if row else None


def save_url(long_url: str, short_code: str) -> str:
    """Insert a new short URL row and return its created_at timestamp."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO links (long_url, short_code, click_count, created_at)
            VALUES (?, ?, 0, CURRENT_TIMESTAMP)
            """,
            (long_url, short_code),
        )
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "SELECT created_at FROM links WHERE short_code = ?",
                (short_code,),
            )
            row = cursor.fetchone()
        conn.commit()
        return row[0]


def get_link_by_code(short_code: str) -> Optional[tuple[str, int]]:
    """Return long_url and click_count for a short code, or None if missing."""
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "SELECT long_url, click_count FROM links WHERE short_code = ?",
                (short_code,),
            )
            row = cursor.fetchone()
            return (row[0], row[1]) if row else None


def increment_click_count(short_code: str) -> None:
    """Increment click_count by 1 for the given short code."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE links SET click_count = click_count + 1 WHERE short_code = ?",
            (short_code,),
        )
        conn.commit()


def get_all_links() -> list[tuple[str, str, int, str]]:
    """Return all stored URLs ordered by most recent first."""
    with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                SELECT long_url, short_code, click_count, created_at
                FROM links
                ORDER BY id DESC
                """
            )
            return cursor.fetchall()

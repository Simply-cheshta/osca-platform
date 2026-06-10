import sqlite3
from pathlib import Path

from app.core.config import settings


def run_sqlite_migrations() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = Path(__file__).resolve().parents[2] / db_path[2:]
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "bookmarked_issues" in tables:
            cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(bookmarked_issues)").fetchall()
            }
            for name, col_type in [
                ("user_id", "INTEGER"),
                ("match_score", "INTEGER"),
                ("difficulty", "VARCHAR(20)"),
                ("created_at", "DATETIME"),
            ]:
                if name not in cols:
                    conn.execute(
                        f"ALTER TABLE bookmarked_issues ADD COLUMN {name} {col_type}"
                    )

        conn.commit()
    finally:
        conn.close()

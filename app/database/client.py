"""Database client menggunakan PyMySQL + SQLAlchemy.

Di development bisa pakai SQLite, di container/production pakai MySQL.
"""
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from app.core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_IS_LOCAL, SQLITE_PATH


def _mysql_url() -> str:
    user = quote_plus(DB_USER)
    pw = quote_plus(DB_PASSWORD)
    return f"mysql+pymysql://{user}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class DBClient:
    def __init__(self):
        if DB_IS_LOCAL:
            db_path = Path(__file__).resolve().parent.parent.parent / SQLITE_PATH
            self.engine = create_engine(f"sqlite:///{db_path}")
        else:
            self.engine = create_engine(_mysql_url())

    def execute(self, sql: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

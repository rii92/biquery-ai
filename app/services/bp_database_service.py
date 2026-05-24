"""Database service khusus BP Batam (Oracle).

Menggabungkan template resolver, validator, dan BPClient.
Engine dibuat lazy (hanya saat execute pertama).
"""

import re

from app.database.bp_client import BPClient
from app.intents.loader import get_intent
from app.sql.validator import SQLValidator


class DatabaseConnectionError(Exception):
    pass


class BPDatabaseService:
    def __init__(self):
        self.validator = SQLValidator()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = BPClient()
        return self._client

    def generate_sql(self, payload: dict) -> str:
        intent_id = payload.get("intent", "")
        meta = get_intent(intent_id)
        if not meta:
            return ""
        sql = meta["sql_template"]
        for key, value in payload.items():
            if key in ("intent",):
                continue
            sql = sql.replace(f"{{{key}}}", str(value))
        sql = re.sub(r"\{\w+\}", "1 = 1", sql)
        return sql

    def validate_sql(self, sql: str) -> bool:
        return bool(sql) and self.validator.validate(sql)

    def execute(self, sql: str):
        try:
            return self.client.execute(sql)
        except Exception as e:
            raise DatabaseConnectionError(
                f"Gagal terhubung ke database BP Batam: {e}"
            ) from e

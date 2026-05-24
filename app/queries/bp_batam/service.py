"""Service layer untuk eksekusi query BP Batam Data Warehouse.

Menggabungkan template query dari modul queries dengan BPClient (Oracle).
"""

import re

from app.database.bp_client import BPClient
from app.queries.bp_batam.executive_summary import get_query, list_queries


class BPService:
    def __init__(self):
        self.client = BPClient()

    def resolve_query(self, query_id: str, filters: dict | None = None) -> str:
        meta = get_query(query_id)
        if not meta:
            raise ValueError(f"Query '{query_id}' tidak ditemukan")
        sql = meta["sql"]
        if filters:
            for key, value in filters.items():
                placeholder = "{{" + key + "}}"
                if placeholder in sql:
                    sql = sql.replace(placeholder, str(value))
        sql = re.sub(r"\{\{\w+\}\}", "1 = 1", sql)
        return sql

    def run(self, query_id: str, filters: dict | None = None) -> list[dict]:
        sql = self.resolve_query(query_id, filters)
        return self.client.execute(sql)

    def list_available(self) -> list[dict]:
        return list_queries()

"""Database service wrapping template engine, validator, and execution.

Keeps the API layer oblivious to implementation details.
"""
from app.sql.template_engine import SQLTemplateEngine
from app.sql.validator import SQLValidator
from app.database.client import DBClient


class DatabaseService:
    def __init__(self):
        self.engine = SQLTemplateEngine()
        self.validator = SQLValidator()
        self.db = DBClient()

    def generate_sql(self, payload: dict) -> str:
        return self.engine.generate(payload)

    def validate_sql(self, sql: str) -> bool:
        return bool(sql) and self.validator.validate(sql)

    def execute(self, sql: str):
        return self.db.execute(sql)

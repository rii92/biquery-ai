"""Application configuration loaded from .env via python-dotenv."""

import os

import dotenv

dotenv.load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "db_eduquery")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
SQLITE_PATH = os.getenv("SQLITE_PATH", "database/eduquery.db")
ACADEMIC_YEARS = os.getenv("ACADEMIC_YEARS", "2023/2024,2024/2025,2025/2026").split(",")

_db_is_local_env = os.getenv("DB_IS_LOCAL")
if _db_is_local_env is not None:
    DB_IS_LOCAL = _db_is_local_env.lower() in ("1", "true", "yes")
else:
    DB_IS_LOCAL = DB_HOST in ("localhost", "127.0.0.1")

# ── BP Batam Data Warehouse ───────────────────────────
BP_DB_USER = os.getenv("BP_DB_USER", "us_dwh")
BP_DB_PASSWORD = os.getenv("BP_DB_PASSWORD", "DeWeHaRS20DuaFive")
BP_DB_HOST = os.getenv("BP_DB_HOST", "bpdb-scan.bpbatam.go.id:1521")
BP_DB_SERVICE_NAME = os.getenv("BP_DB_SERVICE_NAME", "begs")

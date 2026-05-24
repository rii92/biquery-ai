"""Konfigurasi Pytest — paksa SQLite untuk pengujian lokal."""
import os

# Override SEBELUM import app apa pun agar config.py membaca ini.
# dotenv.load_dotenv() tidak akan override env var yang sudah ada secara default.
os.environ.setdefault("DB_IS_LOCAL", "true")

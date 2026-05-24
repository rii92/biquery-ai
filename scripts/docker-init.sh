#!/usr/bin/env bash
# EduQuery AI — Container init Docker
# Menjalankan migrasi DB lalu keluar.
# Dipanggil oleh service "init" di docker-compose.
set -e

echo "[init] Menjalankan migrasi database..."
uv run python -m app.database.migrate

echo "[init] Init selesai."

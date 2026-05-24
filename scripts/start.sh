#!/usr/bin/env bash
set -e

echo "[start] Menjalankan FastAPI..."
HOST="${APP_HOST:?APP_HOST harus diisi di .env}"
PORT="${APP_PORT:?APP_PORT harus diisi di .env}"
exec uv run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload

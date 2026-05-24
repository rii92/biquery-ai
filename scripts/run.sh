#!/usr/bin/env bash
# EduQuery AI — Penjalan terpadu
# Pemakaian:
#   ./scripts/run.sh docker  Bangun & jalankan semua container
#   ./scripts/run.sh init    Pull model Ollama + migrasi DB (lokal)
#   ./scripts/run.sh start   Jalankan server FastAPI (lokal)
#   ./scripts/run.sh test    Jalankan test suite
#   ./scripts/run.sh restart Restart container app (ambil perubahan kode)
#   ./scripts/run.sh logs    Lihat log container app
#   ./scripts/run.sh stop    Hentikan semua container
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

load_env() {
    set -a
    [ -f "$PROJECT_ROOT/.env" ] && source "$PROJECT_ROOT/.env"
    set +a
}

cd "$PROJECT_ROOT"

case "${1:-help}" in
    docker|up)
        echo "[run] Building & starting Docker containers..."
        docker compose up --build
        ;;
    docker-init)
        echo "[run] Running init container (migrate DB)..."
        docker compose run --rm init
        ;;
    init)
        load_env
        if command -v ollama &> /dev/null; then
            MODEL="${OLLAMA_MODEL}"
            if [ -z "$MODEL" ]; then
                echo "[run] ERROR: OLLAMA_MODEL tidak diset di .env"
                exit 1
            fi
            if ollama list 2>/dev/null | grep -qi "^${MODEL}[[:space:]]"; then
                echo "[run] Model ${MODEL} sudah tersedia, skip pull."
            else
                echo "[run] Pulling model ${MODEL}..."
                ollama pull "$MODEL"
            fi
        else
            echo "[run] Ollama CLI not found. Install from https://ollama.com"
        fi
        echo "[run] Running database migration..."
        uv run python -m app.database.migrate
        echo "[run] Init complete."
        ;;
    start|dev)
        load_env
        HOST="${APP_HOST:-0.0.0.0}"
        PORT="${APP_PORT:-8000}"
        echo "[run] Starting FastAPI on ${HOST}:${PORT}..."
        uv run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
        ;;
    test)
        echo "[run] Running tests..."
        uv run pytest
        ;;
    restart)
        echo "[run] Restarting app container..."
        docker compose restart app
        ;;
    logs)
        echo "[run] Tailing app container logs..."
        docker compose logs -f app
        ;;
    stop)
        echo "[run] Stopping all containers..."
        docker compose down
        ;;
    *)
        echo "Usage: $0 {docker|docker-init|init|start|test|restart|logs|stop}"
        echo ""
        echo "  docker       Build & start all services via Docker Compose"
        echo "  docker-init  Run init container (migrate DB) manually"
        echo "  init         Pull Ollama model & run DB migration (local)"
        echo "  start        Run FastAPI dev server (local)"
        echo "  test         Run pytest suite"
        echo "  restart      Restart app container (pick up code changes)"
        echo "  logs         Tail app container logs"
        echo "  stop         docker compose down"
        ;;
esac

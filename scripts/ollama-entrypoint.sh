#!/usr/bin/env bash
set -e

export OLLAMA_HOST=0.0.0.0

# Jalankan server Ollama di latar belakang
ollama serve &
SERVER_PID=$!

# Client pakai localhost (bukan 0.0.0.0)
export OLLAMA_HOST=http://localhost:11434

# Tunggu server siap
echo "[ollama] Menunggu server siap..."
until ollama list >/dev/null 2>&1; do sleep 1; done
echo "[ollama] Server siap."

# Tarik model — OLLAMA_MODEL harus diset via .env
MODEL="${OLLAMA_MODEL:?OLLAMA_MODEL harus diisi di .env}"
if ollama list 2>/dev/null | grep -qi "^${MODEL}[[:space:]]"; then
  echo "[ollama] Model ${MODEL} sudah ada, skip pull."
else
  echo "[ollama] Pulling model ${MODEL}..."
  ollama pull "${MODEL}"
  echo "[ollama] Model ${MODEL} siap."
fi

# Pertahankan server di latar depan
wait $SERVER_PID

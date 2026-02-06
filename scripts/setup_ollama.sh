#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama not found. Install from https://ollama.com/install.sh"
  exit 1
fi

BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
GENERAL_MODEL=${GENERAL_MODEL:-llama3.1:8b}
CODE_MODEL=${CODE_MODEL:-qwen2.5-coder:7b}

check_service() {
  curl -fsSL "$BASE_URL/api/tags" >/dev/null 2>&1
}

if ! check_service; then
  echo "Ollama service unreachable; attempting to start it..."
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user start ollama || true
    sleep 2
  fi
  if ! check_service && command -v ollama >/dev/null 2>&1; then
    nohup ollama serve --port 11434 --listen http://localhost:11434 >/tmp/ollama.log 2>&1 &
    sleep 3
  fi
fi

ollama pull "$GENERAL_MODEL"
ollama pull "$CODE_MODEL"

if check_service; then
  echo "Ollama ready"
else
  echo "Failed to verify Ollama after pulling models; review logs."
  exit 1
fi

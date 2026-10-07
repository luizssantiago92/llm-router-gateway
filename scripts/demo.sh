#!/bin/sh
# Curl sequence for the local zero-key demo.
# Start first: docker compose -f compose.demo.yml up --build
set -eu

base="${DEMO_BASE_URL:-http://127.0.0.1:8000}"
key="${GATEWAY_API_KEY:-demo}"

chat() {
  curl -fsS "$base/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $key" \
    -d "$1"
  echo
}

echo "health"
curl -fsS "$base/health"
echo

echo "simple"
chat '{"messages":[{"role":"user","content":"hello"}],"temperature":0,"max_tokens":16}'

echo "repeat"
chat '{"messages":[{"role":"user","content":"hello"}],"temperature":0,"max_tokens":16}'

echo "local failure falls back to cloud"
chat '{"messages":[{"role":"user","content":"hello simulate-local-failure"}],"temperature":0,"max_tokens":16}'

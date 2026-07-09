#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.factory-runtime"
BACKEND_PID_FILE="$RUNTIME_DIR/bus_server.pid"
WEB_PID_FILE="$RUNTIME_DIR/web_ui.pid"
BACKEND_LOG="$RUNTIME_DIR/bus_server.log"
WEB_LOG="$RUNTIME_DIR/web_ui.log"

mkdir -p "$RUNTIME_DIR"

if ss -ltn "( sport = :9999 or sport = :8080 )" | grep -q LISTEN; then
  echo "Los puertos 9999 o 8080 ya estan en uso. Cierra las instancias previas antes de continuar."
  exit 1
fi

cd "$ROOT_DIR"

python3 -m src.server.bus_server >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >"$BACKEND_PID_FILE"

python3 -m src.client.web_client_server >"$WEB_LOG" 2>&1 &
WEB_PID=$!
echo "$WEB_PID" >"$WEB_PID_FILE"

cleanup() {
  kill "$WEB_PID" "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

for _ in $(seq 1 30); do
  if python3 - <<'PY'
import sys
import urllib.request

for url in ("http://127.0.0.1:8080/api/health",):
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            if response.status == 200:
                sys.exit(0)
    except Exception:
        pass
sys.exit(1)
PY
  then
    break
  fi
  sleep 0.5
done

echo "Backend TCP: 127.0.0.1:9999 (PID $BACKEND_PID)"
echo "Interfaz web: http://127.0.0.1:8080 (PID $WEB_PID)"
echo "La primera sesion del navegador se conectara y precargara datos automaticamente."
echo "Presiona Ctrl+C en esta terminal para detener ambos procesos."

wait "$WEB_PID"

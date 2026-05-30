#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"

RESET_DB=0
NO_INSTALL=0

for arg in "$@"; do
  case "$arg" in
    --reset-db)
      RESET_DB=1
      ;;
    --no-install)
      NO_INSTALL=1
      ;;
    -h|--help)
      echo "Usage: scripts/run_project.sh [--reset-db] [--no-install]"
      echo ""
      echo "Options:"
      echo "  --reset-db    Recreate SQLite database with seed data before starting"
      echo "  --no-install  Skip dependency installation check"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Run scripts/run_project.sh --help for usage."
      exit 1
      ;;
  esac
done

info() {
  printf "\033[1;34m[info]\033[0m %s\n" "$1"
}

ok() {
  printf "\033[1;32m[ok]\033[0m %s\n" "$1"
}

fail() {
  printf "\033[1;31m[error]\033[0m %s\n" "$1" >&2
}

find_free_port() {
  local _host="$1"
  local start_port="$2"
  local port

  if ! command -v lsof >/dev/null 2>&1; then
    echo "$start_port"
    return
  fi

  for port in $(seq "$start_port" "$((start_port + 49))"); do
    if ! lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "$port"
      return
    fi
  done

  fail "No free port found from $start_port to $((start_port + 49))"
  exit 1
}

cleanup() {
  info "Stopping servers..."
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

cd "$ROOT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  info "Creating virtual environment at .venv"
  python3 -m venv "$ROOT_DIR/.venv"
fi

if [[ "$NO_INSTALL" -eq 0 ]]; then
  info "Installing dependencies from backend/requirements.txt"
  "$PYTHON_BIN" -m pip install -r "$ROOT_DIR/backend/requirements.txt"
fi

if [[ "$RESET_DB" -eq 1 || ! -f "$ROOT_DIR/backend/rescue_system.db" ]]; then
  info "Importing seed data into SQLite database"
  "$PYTHON_BIN" "$ROOT_DIR/backend/generate_seed_data.py"
fi

ACTUAL_BACKEND_PORT="$(find_free_port "$BACKEND_HOST" "$BACKEND_PORT")"
ACTUAL_FRONTEND_PORT="$(find_free_port "0.0.0.0" "$FRONTEND_PORT")"

if [[ "$ACTUAL_BACKEND_PORT" != "$BACKEND_PORT" ]]; then
  info "Backend port $BACKEND_PORT is busy; using $ACTUAL_BACKEND_PORT instead"
fi

if [[ "$ACTUAL_FRONTEND_PORT" != "$FRONTEND_PORT" ]]; then
  info "Frontend port $FRONTEND_PORT is busy; using $ACTUAL_FRONTEND_PORT instead"
fi

info "Starting backend on http://$BACKEND_HOST:$ACTUAL_BACKEND_PORT"
"$PYTHON_BIN" -m uvicorn app.main:app --app-dir "$ROOT_DIR/backend" --host "$BACKEND_HOST" --port "$ACTUAL_BACKEND_PORT" &
BACKEND_PID=$!

info "Starting frontend on http://localhost:$ACTUAL_FRONTEND_PORT"
(
  cd "$ROOT_DIR/frontend"
  BACKEND_URL="http://$BACKEND_HOST:$ACTUAL_BACKEND_PORT/api/v1" FRONTEND_PORT="$ACTUAL_FRONTEND_PORT" "$PYTHON_BIN" main.py
) &
FRONTEND_PID=$!

ok "Backend API: http://$BACKEND_HOST:$ACTUAL_BACKEND_PORT"
ok "API docs:    http://$BACKEND_HOST:$ACTUAL_BACKEND_PORT/docs"
ok "Frontend:    http://localhost:$ACTUAL_FRONTEND_PORT"
info "Press Ctrl+C to stop both servers."

wait "$BACKEND_PID" "$FRONTEND_PID"

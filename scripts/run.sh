#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo "Python 3 belum terpasang."; exit 1; }
command -v node >/dev/null || { echo "Node.js belum terpasang."; exit 1; }
command -v npm >/dev/null || { echo "npm belum terpasang."; exit 1; }
if [ ! -d backend/.venv ]; then python3 -m venv backend/.venv; fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install); fi
mkdir -p backend/data
export SIBERWASPADA_DB="${SIBERWASPADA_DB:-$ROOT/backend/data/siberwaspada.sqlite3}"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
API_PID=$!
cleanup(){ kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
echo "SIBERWASPADA AI aktif:"
echo "  Dasbor: http://127.0.0.1:5173"
echo "  API:    http://127.0.0.1:8000/docs"
(cd frontend && npm run dev -- --host 127.0.0.1)

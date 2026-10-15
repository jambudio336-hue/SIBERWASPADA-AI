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
# Termux mengelola pip melalui pkg; meng-upgrade pip sendiri dapat merusak instalasi Python.
if [[ "${PREFIX:-}" != /data/data/com.termux/files/usr* ]]; then
  python -m pip install --upgrade pip
fi
pip install -r backend/requirements.txt
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install); fi
mkdir -p backend/data
export SIBERWASPADA_DB="${SIBERWASPADA_DB:-$ROOT/backend/data/siberwaspada.sqlite3}"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
API_PID=$!
cleanup(){ kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
API_READY=0
for _ in $(seq 1 30); do
  if python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1)' >/dev/null 2>&1; then
    API_READY=1
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "Backend gagal dijalankan. Periksa pesan error di atas dan pastikan port 8000 tidak sedang dipakai."
    exit 1
  fi
  sleep 1
done
if [ "$API_READY" -ne 1 ]; then
  echo "Backend tidak merespons dalam 30 detik. Pastikan port 8000 tersedia."
  exit 1
fi
echo "SIBERWASPADA AI aktif:"
echo "  Dasbor: http://127.0.0.1:5173"
echo "  API:    http://127.0.0.1:8000/docs"
(cd frontend && npm run dev -- --host 127.0.0.1)

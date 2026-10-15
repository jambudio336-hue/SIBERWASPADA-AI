#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
pkg update -y
pkg install -y python nodejs
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python -m pip install --upgrade pip
python -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
(cd frontend && npm install)
mkdir -p backend/data
echo "Selesai. Jalankan: bash scripts/run.sh"
echo "Jika penyimpanan repo berada di /sdcard, pindahkan ke $HOME terlebih dahulu agar npm/venv bekerja stabil."

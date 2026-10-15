#!/usr/bin/env bash
set -Eeuo pipefail
if command -v apt-get >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-pip nodejs npm
elif command -v dnf >/dev/null; then
  sudo dnf install -y python3 python3-pip nodejs npm
elif command -v pacman >/dev/null; then
  sudo pacman -Sy --needed python python-pip nodejs npm
else
  echo "Paket manajer tidak dikenali. Pasang Python 3.11+ dan Node.js 20+ secara manual."
  exit 1
fi
"$(dirname "$0")/run.sh"

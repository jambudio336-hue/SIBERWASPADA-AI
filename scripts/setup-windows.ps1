$ErrorActionPreference = "Stop"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Pasang Python 3.11+ dari https://www.python.org/downloads/windows/ dan aktifkan opsi Add Python to PATH." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Pasang Node.js 20 LTS dari https://nodejs.org/." }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
if (-not (Test-Path "backend/.venv")) { python -m venv backend/.venv }
& "backend/.venv/Scripts/python.exe" -m pip install --upgrade pip
& "backend/.venv/Scripts/pip.exe" install -r backend/requirements.txt
Push-Location frontend
npm install
Pop-Location
Write-Host "Instalasi dependensi selesai. Jalankan: powershell -ExecutionPolicy Bypass -File scripts/run.ps1" -ForegroundColor Green

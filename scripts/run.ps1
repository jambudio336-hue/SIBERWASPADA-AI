$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11+ belum terpasang. Pasang dari python.org." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js 20+ belum terpasang. Pasang dari nodejs.org." }
if (-not (Test-Path "backend/.venv")) { python -m venv backend/.venv }
& "backend/.venv/Scripts/python.exe" -m pip install --upgrade pip
& "backend/.venv/Scripts/pip.exe" install -r backend/requirements.txt
if (-not (Test-Path "frontend/node_modules")) { Push-Location frontend; npm install; Pop-Location }
New-Item -ItemType Directory -Force -Path "backend/data" | Out-Null
$env:SIBERWASPADA_DB = Join-Path $Root "backend/data/siberwaspada.sqlite3"
$Api = Start-Process -FilePath "backend/.venv/Scripts/python.exe" -ArgumentList @("-m","uvicorn","app.main:app","--app-dir","backend","--host","127.0.0.1","--port","8000") -PassThru -NoNewWindow
try {
  Write-Host "Dasbor: http://127.0.0.1:5173" -ForegroundColor Cyan
  Write-Host "API:    http://127.0.0.1:8000/docs" -ForegroundColor Cyan
  Set-Location frontend
  npm run dev -- --host 127.0.0.1
} finally {
  if ($Api -and -not $Api.HasExited) { Stop-Process -Id $Api.Id -Force }
}

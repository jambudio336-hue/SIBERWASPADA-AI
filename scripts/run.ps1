$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11+ belum terpasang. Pasang dari python.org." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js 20+ belum terpasang. Pasang dari nodejs.org." }
if (-not (Test-Path "backend/.venv")) { python -m venv backend/.venv }
$PythonExe = Join-Path $Root "backend/.venv/Scripts/python.exe"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r backend/requirements.txt
if (-not (Test-Path "frontend/node_modules")) { Push-Location frontend; try { npm install } finally { Pop-Location } }
New-Item -ItemType Directory -Force -Path "backend/data" | Out-Null
$env:SIBERWASPADA_DB = Join-Path $Root "backend/data/siberwaspada.sqlite3"
$Api = Start-Process -FilePath $PythonExe -ArgumentList @("-m","uvicorn","app.main:app","--app-dir","backend","--host","127.0.0.1","--port","8000") -PassThru -NoNewWindow
try {
  $Ready = $false
  for ($i = 0; $i -lt 30; $i++) {
    if ($Api.HasExited) { throw "Backend berhenti saat startup. Pastikan port 8000 tersedia." }
    try {
      $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2
      if ($Health.status -eq "ok") { $Ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
  }
  if (-not $Ready) { throw "Backend tidak merespons dalam 30 detik. Pastikan port 8000 tersedia." }
  Write-Host "Dasbor: http://127.0.0.1:5173" -ForegroundColor Cyan
  Write-Host "API:    http://127.0.0.1:8000/docs" -ForegroundColor Cyan
  Set-Location frontend
  npm run dev -- --host 127.0.0.1
} finally {
  if ($Api -and -not $Api.HasExited) { Stop-Process -Id $Api.Id -Force }
}

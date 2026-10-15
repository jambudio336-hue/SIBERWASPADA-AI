# SIBERWASPADA AI 🇮🇩

Platform edukasi dan pemantauan keamanan siber dengan mesin deteksi berbasis aturan, dashboard insiden, API FastAPI, database SQLite, dan simulator kejadian aman.

> **Transparansi data:** data yang dibuat tombol **Jalankan simulasi** adalah data demo, bukan telemetri jaringan nyata. Pemantauan produksi memerlukan konektor/sumber log yang sah dan dikonfigurasi secara eksplisit.

## Fitur MVP
- Dashboard ringkasan event, alert, dan tingkat keparahan.
- REST API FastAPI + dokumentasi OpenAPI otomatis.
- Penyimpanan SQLite lokal untuk event dan insiden.
- Deteksi aturan: percobaan login berulang, lonjakan request, dan pola akses mencurigakan.
- Simulator skenario defensif yang tidak mengirim trafik ke target eksternal.
- Filter event berdasarkan tingkat keparahan dan pencarian teks/IP/event.
- Perubahan status insiden, ekspor CSV kejadian maupun insiden.
- Impor log JSONL (maks. 1 MB dan 500 baris), validasi seluruh batch sebelum penyimpanan.
- Jejak audit tindakan sistem/operator dan tren kejadian harian 1–30 hari.
- Endpoint laporan ringkas dan katalog aturan deteksi yang dapat dijelaskan.
- Pengujian backend dan GitHub Actions CI.
- Tidak memerlukan API key berbayar untuk fitur inti.

## Arsitektur
- `frontend/`: React + TypeScript + Vite.
- `backend/`: Python + FastAPI + SQLite.
- `backend/data/`: database runtime (tidak dikomit).
- `.github/workflows/ci.yml`: tes backend dan build frontend.
- `.github/workflows/desktop-build.yml`: paket desktop Windows/macOS/Linux.
- `scripts/`: skrip instalasi dan peluncuran lintas platform.
- `frontend/public/`: manifest PWA, ikon, dan cache kerangka offline.

## Instalasi lintas platform

### Termux (Android)
Klon repo ke direktori home Termux (hindari /sdcard agar izin berkas dan symlink tidak bermasalah):
```bash
pkg update -y && pkg install -y git
git clone https://github.com/jambudio336-hue/SIBERWASPADA-AI.git
cd SIBERWASPADA-AI
bash scripts/setup-termux.sh
bash scripts/run.sh
```
Buka `http://127.0.0.1:5173` di browser Android. Termux harus tetap berjalan agar layanan API aktif.

### Kali Linux / Ubuntu / Debian
```bash
git clone https://github.com/jambudio336-hue/SIBERWASPADA-AI.git
cd SIBERWASPADA-AI
bash scripts/setup-linux.sh
```
Setelah dependensi terpasang, jalankan `bash scripts/run.sh` untuk memulai aplikasi.

### macOS
Pasang Python 3.11+ dan Node.js 20+ (misalnya melalui Homebrew), lalu jalankan:
```bash
git clone https://github.com/jambudio336-hue/SIBERWASPADA-AI.git
cd SIBERWASPADA-AI
bash scripts/run.sh
```

### Windows 10/11 (PowerShell)
Pasang Python 3.11+ dan Node.js 20+, lalu jalankan dari folder repo:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-windows.ps1
.\scripts\run.ps1
```

### Installer desktop siap pakai
Alur GitHub Actions membangun installer Windows `.exe`, macOS `.dmg`, serta Linux `.AppImage` dan `.deb`. Paket desktop dirancang menyertakan frontend dan API lokal dengan basis data di folder data pengguna. Buka tab **Actions** untuk melihat status build dan mengunduh artefak; setelah rilis dengan tag `v*`, berkas juga dipasang ke GitHub Releases. Installer baru tersedia setelah alur build berhasil dijalankan.

### Instal sebagai aplikasi web (PWA)
Buka frontend melalui `localhost` atau situs HTTPS pada browser yang mendukung PWA, lalu pilih **Instal aplikasi** atau **Tambahkan ke layar utama**. PWA menyimpan kerangka antarmuka untuk akses offline; data dinamis tetap memerlukan layanan backend yang berjalan.

## Jalankan lokal
Persyaratan: Python 3.11+ dan Node.js 20+.

### 1. Backend
```bash
cd backend
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
API: http://127.0.0.1:8000  
Dokumentasi API: http://127.0.0.1:8000/docs

### 2. Frontend (terminal kedua)
```bash
cd frontend
npm install
npm run dev
```
Buka URL Vite yang ditampilkan. Frontend menggunakan API di `http://127.0.0.1:8000` secara default. Atur `VITE_API_URL` jika API berada di alamat lain.

### 3. Tes backend
```bash
cd backend
pip install -r requirements.txt
pytest -q
```

### 4. Jalankan seluruh stack dengan Docker
Jika Docker dan Docker Compose sudah terpasang:
```bash
docker compose up --build
```
Frontend: http://localhost:8080  
Backend: http://localhost:8000  
API docs: http://localhost:8000/docs

Data SQLite disimpan dalam named volume Docker `siberwaspada_data` sehingga tetap ada saat container dibuat ulang. Untuk menghentikan layanan: `docker compose down` (volume data tidak dihapus). Untuk menghapus data juga: `docker compose down -v`.

## Endpoint utama
- `GET /api/health`
- `GET /api/metrics`
- `GET /api/events?limit=100&severity=high`
- `GET /api/alerts`
- `GET /api/rules` — katalog aturan deteksi aktif.
- `GET /api/trends?days=7` — tren harian kejadian (1–30 hari).
- `GET /api/audit?limit=100` — jejak audit terbaru.
- `POST /api/import/jsonl` — impor JSON Lines melalui badan teks.
- `GET /api/reports/summary` — ringkasan status/severitas insiden dan langkah tindak lanjut.
- `GET /api/export/incidents.csv` — unduh laporan insiden.
- `POST /api/simulator/run` — membuat event demo lokal.
- `PATCH /api/incidents/{id}` — ubah status insiden.
- `GET /api/export/events.csv`

## Batasan keamanan MVP
- Ini adalah MVP untuk demonstrasi dan pengembangan, belum SIEM produksi.
- Belum ada autentikasi multi-pengguna; jangan mengekspos API langsung ke internet.
- Jangan memasukkan data pribadi atau log sensitif ke demo publik.
- Integrasi log nyata harus memiliki otorisasi, validasi input, kontrol akses, retensi, dan audit.
- AI generatif bersifat opsional dan tidak dibutuhkan mesin deteksi inti.

## Roadmap
1. Tambah autentikasi/RBAC sebelum dipakai multi-pengguna atau diekspos ke jaringan.
2. Tambah konektor observability yang disahkan dan pengelolaan retensi.
3. Evaluasi false positive/false negative dengan dataset sintetis.
4. Deploy dengan HTTPS, pengelolaan rahasia, backup, dan pemantauan.

## Lisensi
MIT — lihat `LICENSE`.

const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");

let apiProcess;
let mainWindow;
const port = "8000";
const baseUrl = "http://127.0.0.1:" + port;

function backendExecutable() {
  const name = process.platform === "win32" ? "siberwaspada-api.exe" : "siberwaspada-api";
  return path.join(process.resourcesPath, "backend", name);
}

async function waitForApi(timeoutMs = 25000) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    try {
      const response = await fetch(baseUrl + "/api/health");
      if (response.ok) return true;
    } catch (_) {}
    await new Promise(resolve => setTimeout(resolve, 350));
  }
  return false;
}

async function createWindow() {
  const executable = backendExecutable();
  if (!fs.existsSync(executable)) {
    dialog.showErrorBox("Komponen layanan tidak ditemukan", "Berkas layanan SIBERWASPADA AI tidak ditemukan. Unduh paket desktop lengkap dari GitHub Releases.");
    app.quit();
    return;
  }
  const dataDir = path.join(app.getPath("userData"), "data");
  fs.mkdirSync(dataDir, { recursive: true });
  const env = {
    ...process.env,
    SIBERWASPADA_DB: path.join(dataDir, "siberwaspada.sqlite3"),
    SIBERWASPADA_WEB_DIR: path.join(process.resourcesPath, "app", "web"),
    SIBERWASPADA_PORT: port
  };
  apiProcess = spawn(executable, [], { env, stdio: "ignore", windowsHide: true });
  apiProcess.on("error", error => console.error("Gagal menjalankan layanan:", error.message));
  const ready = await waitForApi();
  if (!ready) {
    dialog.showErrorBox("Layanan tidak siap", "API lokal tidak merespons. Periksa apakah port 8000 sedang dipakai, lalu coba jalankan kembali.");
    app.quit();
    return;
  }
  mainWindow = new BrowserWindow({
    width: 1440, height: 920, minWidth: 900, minHeight: 640,
    backgroundColor: "#07111f",
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true }
  });
  await mainWindow.loadURL(baseUrl);
  mainWindow.on("closed", () => { mainWindow = null; });
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
app.on("before-quit", () => {
  if (apiProcess && !apiProcess.killed) apiProcess.kill();
});

export function registerPwa() {
  if ("serviceWorker" in navigator && import.meta.env.PROD) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(error => {
        console.warn("Pendaftaran mode instalasi gagal:", error);
      });
    });
  }
}

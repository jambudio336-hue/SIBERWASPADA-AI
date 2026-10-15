import { useEffect, useRef, useState } from "react";
import { ClipboardList, FileUp, TrendingUp } from "lucide-react";

type Trend = { date: string; total: number; critical: number; high: number; simulated: number };
type Audit = { id: number; timestamp: string; action: string; entity_type: string; entity_id: string; actor: string; details: string };

export default function AdvancedPanel({ api }: { api: string }) {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const load = async () => {
    try {
      const [t, a] = await Promise.all([
        fetch(api + "/api/trends?days=7"),
        fetch(api + "/api/audit?limit=8"),
      ]);
      if (!t.ok || !a.ok) throw new Error("Data fitur lanjutan belum tersedia dari layanan API.");
      const trendData = await t.json();
      setTrends(trendData.items || []);
      setAudit(await a.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal memuat data lanjutan.");
    }
  };

  useEffect(() => { void load(); }, []);

  const importFile = async (file?: File) => {
    if (!file) return;
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await fetch(api + "/api/import/jsonl", {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: await file.text(),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Impor gagal.");
      setMessage("Impor berhasil: " + result.berhasil + " baris tersimpan.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Impor log gagal.");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  };

  const dateLabel = (value: string) => {
    try { return new Date(value).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "short" }); }
    catch { return value; }
  };
  const maxTotal = Math.max(1, ...trends.map(item => item.total));

  return <section className="advanced-section">
    <div className="advanced-toolbar">
      <div><b>Fitur lanjutan</b><span>Tren, jejak audit, dan impor log yang tervalidasi</span></div>
      <input ref={input} type="file" accept=".jsonl,.ndjson,.txt" hidden onChange={e => void importFile(e.target.files?.[0])} />
      <button className="secondary-button" onClick={() => input.current?.click()} disabled={busy}><FileUp size={15} /> {busy ? "Mengimpor..." : "Impor log JSONL"}</button>
    </div>
    {message && <div className="advanced-message">{message}</div>}
    {error && <div className="advanced-error">{error}</div>}
    <div className="advanced-grid">
      <section className="panel trend-panel" id="tren-keamanan">
        <div className="panel-heading"><div><h2><TrendingUp size={18} /> Tren kejadian 7 hari</h2><p>Hitungan harian dari basis data lokal</p></div></div>
        <div className="trend-list">{trends.length ? trends.map(item => <div className="trend-row" key={item.date}>
          <span className="trend-date">{item.date}</span>
          <div className="trend-track"><span style={{ width: (item.total / maxTotal * 100) + "%" }} /></div>
          <b>{item.total}</b><small>{item.critical} kritis · {item.high} tinggi · {item.simulated} simulasi</small>
        </div>) : <div className="advanced-empty">Belum ada data tren untuk periode ini.</div>}</div>
        <p className="panel-note">Tren adalah hitungan data tercatat, bukan prediksi atau bukti serangan.</p>
      </section>
      <section className="panel audit-panel" id="jejak-audit">
        <div className="panel-heading"><div><h2><ClipboardList size={18} /> Jejak audit terbaru</h2><p>Catatan tindakan sistem dan perubahan status</p></div><span className="count-badge">{audit.length}</span></div>
        <div className="audit-list">{audit.length ? audit.map(item => <div className="audit-row" key={item.id}>
          <span className="audit-marker" /><div><b>{item.action.replaceAll(".", " · ")}</b><span>{item.entity_type} #{item.entity_id || "—"} · {item.actor}</span>
          <p>{item.details || "Tidak ada rincian tambahan"}</p><small>{dateLabel(item.timestamp)}</small></div>
        </div>) : <div className="advanced-empty">Jejak audit akan muncul setelah ada tindakan.</div>}</div>
      </section>
    </div>
  </section>;
}

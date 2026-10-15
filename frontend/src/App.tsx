import { useCallback, useEffect, useState } from "react";
import AdvancedPanel from "./AdvancedPanel";
import {
  Activity, AlertOctagon, AlertTriangle, ArrowDownToLine, Bell, CheckCircle2,
  CircleHelp, Clock3, Cpu, Database, ExternalLink, FileText, Gauge, Globe2,
  Layers3, LoaderCircle, Play, RefreshCw, Shield, ShieldCheck, Siren, Wifi,
} from "lucide-react";

const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type Metrics = {
  total_events: number;
  simulated_events: number;
  open_incidents: number;
  by_severity: Record<string, number>;
  data_mode: string;
};
type EventItem = {
  id: number; timestamp: string; source_ip: string; event_type: string;
  severity: string; message: string; details: string; is_simulated: number;
};
type Incident = {
  id: number; event_id: number; rule_id: string; title: string; severity: string;
  description: string; recommendation: string; status: string; created_at: string;
  source_ip: string; event_type: string; is_simulated: number;
};

const severityLabel: Record<string, string> = {
  critical: "Kritis", high: "Tinggi", medium: "Sedang", low: "Rendah", info: "Info",
};
const statusLabel: Record<string, string> = {
  open: "Terbuka", investigating: "Diselidiki", resolved: "Selesai", false_positive: "Positif palsu",
};

function timeLabel(value: string) {
  try { return new Date(value).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "medium" }); }
  catch { return value; }
}

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [eventSearch, setEventSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"overview" | "incidents">("overview");
  const [apiOnline, setApiOnline] = useState(false);

  const request = async (path: string, init?: RequestInit) => {
    const response = await fetch(API + path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `API error ${response.status}`);
    }
    return response;
  };

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [m, e, a, h] = await Promise.all([
        request("/api/metrics").then(r => r.json()),
        request("/api/events?limit=100").then(r => r.json()),
        request("/api/alerts").then(r => r.json()),
        request("/api/health").then(r => r.json()),
      ]);
      setMetrics(m); setEvents(e); setIncidents(a); setApiOnline(h.status === "ok");
    } catch (e) {
      setApiOnline(false);
      setError(e instanceof Error ? e.message : "Tidak dapat menghubungi API.");
    }
  }, []);

  useEffect(() => { void refresh(); const id = window.setInterval(() => void refresh(), 12000); return () => window.clearInterval(id); }, [refresh]);

  const runSimulator = async () => {
    setBusy(true); setNotice(""); setError("");
    try {
      const result = await request("/api/simulator/run", { method: "POST" }).then(r => r.json());
      setNotice(`Simulasi selesai: ${result.created} event demo dibuat. Tidak ada trafik dikirim ke target eksternal.`);
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Simulasi gagal dijalankan."); }
    finally { setBusy(false); }
  };

  const changeStatus = async (id: number, status: string) => {
    try {
      await request(`/api/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
      setNotice(`Status insiden #${id} diperbarui menjadi ${statusLabel[status] || status}.`);
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Gagal mengubah status."); }
  };

  const normalizedSearch = eventSearch.trim().toLowerCase();
  const filteredEvents = events.filter(e => (severityFilter === "all" || e.severity === severityFilter) && (!normalizedSearch || [e.message, e.source_ip, e.event_type, e.details].some(value => String(value || "").toLowerCase().includes(normalizedSearch))));
  const openIncidents = incidents.filter(i => i.status === "open" || i.status === "investigating").length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><ShieldCheck size={24} /></div><div><b>SIBER<span>WASPADA</span></b><small>PERTAHANAN SIBER AI</small></div></div>
        <div className="workspace-label">RUANG KERJA</div>
        <button className={`nav-item ${tab === "overview" ? "active" : ""}`} onClick={() => setTab("overview")}><Gauge size={18}/> Ikhtisar <span className="nav-dot"/></button>
        <button className={`nav-item ${tab === "incidents" ? "active" : ""}`} onClick={() => setTab("incidents")}><Siren size={18}/> Insiden <span className="nav-count">{openIncidents}</span></button>
        <div className="workspace-label section-gap">SISTEM</div>
        <button className="nav-item" onClick={() => setNotice("Sumber data nyata belum dikonfigurasi. Dashboard saat ini menggunakan event lokal/demo.")}><Wifi size={18}/> Sumber data</button>
        <button className="nav-item" onClick={() => window.open(API + "/docs", "_blank", "noopener,noreferrer")}><Layers3 size={18}/> Dokumentasi API <ExternalLink size={13} className="nav-end"/></button>
        <button className="nav-item" onClick={() => window.open(API + "/api/export/events.csv", "_blank", "noopener,noreferrer")}><ArrowDownToLine size={18}/> Ekspor event</button>
        <button className="nav-item" onClick={() => window.open(API + "/api/export/incidents.csv", "_blank", "noopener,noreferrer")}><FileText size={18}/> Ekspor insiden</button>
        <button className="nav-item" onClick={() => window.open(API + "/api/reports/summary", "_blank", "noopener,noreferrer")}><Activity size={18}/> Laporan ringkas <ExternalLink size={13} className="nav-end"/></button>
        <div className="sidebar-bottom"><div className="mini-shield"><Shield size={18}/></div><b>Dirancang untuk pertahanan</b><p>Analisis, deteksi, dan respons yang bertanggung jawab.</p><div className="version">SIBERWASPADA · MVP 0.1.0</div></div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">SIBERWASPADA <span>/</span> {tab === "overview" ? "Pusat operasi" : "Manajemen insiden"}</div>
          <div className="top-actions"><div className={`connection ${apiOnline ? "online" : "offline"}`}><span/> {apiOnline ? "API terhubung" : "API terputus"}</div><button className="icon-button" title="Muat ulang data" onClick={() => void refresh()}><RefreshCw size={17}/></button><div className="avatar">SW</div></div>
        </header>

        <section className="page-heading">
          <div><div className="eyebrow"><span className="eyebrow-line"/> PERTAHANAN SIBER INDONESIA</div><h1>{tab === "overview" ? "Pusat Operasi Keamanan" : "Manajemen Insiden"}</h1><p className="subheading">Pantau sinyal keamanan, pahami konteks, dan tindak lanjuti dengan terukur.</p></div>
          <div className="heading-actions"><span className="demo-pill"><span/> MODE LOKAL / DEMO</span><button className="primary-button" onClick={() => void runSimulator()} disabled={busy || !apiOnline}>{busy ? <LoaderCircle size={17} className="spin"/> : <Play size={16}/>} Jalankan simulasi</button></div>
        </section>

        {error && <div className="notice error"><AlertTriangle size={18}/><div><b>Koneksi / permintaan bermasalah</b><p>{error}. Pastikan backend berjalan di {API}.</p></div></div>}
        {notice && <div className="notice success"><CheckCircle2 size={18}/><p>{notice}</p><button onClick={() => setNotice("")} aria-label="Tutup">×</button></div>}
        <div className="data-banner"><CircleHelp size={17}/><div><b>Kejujuran data</b><span>Event demo ditandai sebagai simulasi. Belum ada konektor jaringan produksi yang aktif.</span></div></div>

        {tab === "overview" ? <>
          <div className="stats-grid">
            <StatCard icon={<Activity size={18}/>} label="Total event tercatat" value={metrics?.total_events ?? "—"} detail="Event tersimpan di database lokal" tone="blue"/>
            <StatCard icon={<AlertOctagon size={18}/>} label="Insiden terbuka" value={metrics?.open_incidents ?? "—"} detail="Menunggu tinjauan operator" tone="red"/>
            <StatCard icon={<AlertTriangle size={18}/>} label="Event prioritas tinggi" value={(metrics?.by_severity?.high ?? 0) + (metrics?.by_severity?.critical ?? 0)} detail="Tinggi + kritis" tone="amber"/>
            <StatCard icon={<Database size={18}/>} label="Event simulasi" value={metrics?.simulated_events ?? "—"} detail="Data sintetis untuk demo" tone="purple"/>
          </div>

          <div className="content-grid">
            <section className="panel event-panel">
              <div className="panel-heading"><div><h2><Activity size={18}/> Aliran event keamanan</h2><p>Event terbaru dari API lokal</p></div><button className="text-button" onClick={() => void refresh()}>Segarkan <RefreshCw size={14}/></button></div>
              <div className="filter-row"><span>{filteredEvents.length} event ditampilkan</span><input className="event-search" type="search" value={eventSearch} onChange={e => setEventSearch(e.target.value)} placeholder="Cari IP, event, pesan..." aria-label="Cari event" /><select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} aria-label="Filter tingkat keparahan"><option value="all">Semua tingkat</option><option value="critical">Kritis</option><option value="high">Tinggi</option><option value="medium">Sedang</option><option value="low">Rendah</option><option value="info">Info</option></select></div>
              <div className="table-wrap"><table><thead><tr><th>EVENT</th><th>SUMBER</th><th>SEVERITAS</th><th>WAKTU</th></tr></thead><tbody>
                {filteredEvents.map(event => <tr key={event.id}><td><div className="event-name">{event.message}</div><div className="event-meta">#{event.id} · {event.event_type}{event.is_simulated ? <span className="sim-tag">SIM</span> : null}</div></td><td className="mono">{event.source_ip}</td><td><Severity value={event.severity}/></td><td className="time-cell">{timeLabel(event.timestamp)}</td></tr>)}
                {!filteredEvents.length && <tr><td colSpan={4} className="empty-state"><Activity size={25}/><b>Belum ada event</b><span>Jalankan simulasi untuk membuat data demonstrasi.</span></td></tr>}
              </tbody></table></div>
              <div className="panel-foot"><span><span className="live-dot"/> Sinkronisasi otomatis setiap 12 detik</span><span>{events.length} terbaru · maks. 100</span></div>
            </section>

            <section className="panel side-panel">
              <div className="panel-heading"><div><h2><Bell size={18}/> Tindak lanjut</h2><p>Prioritas operator</p></div><span className="count-badge">{openIncidents}</span></div>
              <div className="incident-list">{incidents.filter(i => i.status === "open" || i.status === "investigating").slice(0, 5).map(item => <div className="incident-item" key={item.id}><div className={`incident-icon ${item.severity}`}>{item.severity === "critical" ? <AlertOctagon size={17}/> : <AlertTriangle size={17}/>}</div><div className="incident-copy"><b>{item.title}</b><span>{item.rule_id} · {item.source_ip}</span><p>{item.recommendation}</p><div className="incident-controls"><select value={item.status} onChange={e => void changeStatus(item.id, e.target.value)} aria-label={`Status insiden ${item.id}`}><option value="open">Terbuka</option><option value="investigating">Diselidiki</option><option value="resolved">Selesai</option><option value="false_positive">False positive</option></select></div></div></div>)}
                {!openIncidents && <div className="empty-side"><CheckCircle2 size={28}/><b>Tidak ada insiden terbuka</b><span>Jalankan simulasi untuk melihat alur respons.</span></div>}
              </div>
              <button className="secondary-button full-button" onClick={() => setTab("incidents")}>Buka semua insiden <ExternalLink size={14}/></button>
            </section>
          </div>

          <div className="bottom-grid">
            <section className="panel rule-panel"><div className="panel-heading"><div><h2><Cpu size={18}/> Mesin deteksi</h2><p>Aturan deterministik dan dapat dijelaskan</p></div><span className="status-tag">AKTIF</span></div>
              <div className="rule-row"><div className="rule-code">AUTH-001</div><div><b>Kegagalan autentikasi</b><span>Menandai event login gagal untuk ditinjau</span></div><Severity value="medium"/></div>
              <div className="rule-row"><div className="rule-code">NET-002</div><div><b>Lonjakan permintaan</b><span>Indikator lonjakan; bukan bukti serangan</span></div><Severity value="high"/></div>
              <div className="rule-row"><div className="rule-code">WEB-003</div><div><b>Pola path mencurigakan</b><span>Indikator traversal pada event web</span></div><Severity value="high"/></div>
              <div className="rule-row"><div className="rule-code">OPS-004</div><div><b>Layanan gagal health check</b><span>Sinyal untuk prosedur pemulihan</span></div><Severity value="critical"/></div>
            </section>
            <section className="panel architecture-panel"><div className="panel-heading"><div><h2><Globe2 size={18}/> Status platform</h2><p>Komponen MVP saat ini</p></div></div>
              <div className="component-row"><span className="component-icon"><Activity size={16}/></span><div><b>REST API</b><span>FastAPI · /api/*</span></div><span className={`health-dot ${apiOnline ? "good" : "bad"}`}/></div>
              <div className="component-row"><span className="component-icon"><Database size={16}/></span><div><b>Penyimpanan</b><span>SQLite lokal</span></div><span className="health-dot good"/></div>
              <div className="component-row"><span className="component-icon"><ShieldCheck size={16}/></span><div><b>Deteksi aturan</b><span>Empat aturan dasar</span></div><span className="health-dot good"/></div>
              <div className="component-row"><span className="component-icon"><FileText size={16}/></span><div><b>Ekspor CSV</b><span>Hingga 500 event terbaru</span></div><span className="health-dot good"/></div>
              <div className="component-row"><span className="component-icon"><Clock3 size={16}/></span><div><b>Refresh dashboard</b><span>Interval 12 detik</span></div><span className="health-dot good"/></div>
            </section>
          </div>
        </> : <section className="panel all-incidents"><div className="panel-heading"><div><h2><Siren size={18}/> Daftar insiden</h2><p>Ubah status setelah operator melakukan tinjauan.</p></div><span className="count-badge">{incidents.length}</span></div>
          <div className="table-wrap"><table><thead><tr><th>INSIDEN</th><th>ATURAN</th><th>SEVERITAS</th><th>STATUS</th><th>AKSI</th></tr></thead><tbody>
            {incidents.map(item => <tr key={item.id}><td><div className="event-name">{item.title}</div><div className="event-meta">Event #{item.event_id} · {item.source_ip}{item.is_simulated ? " · SIMULASI" : ""}</div><div className="incident-description">{item.description}</div><div className="recommendation"><b>Rekomendasi:</b> {item.recommendation}</div></td><td className="mono">{item.rule_id}</td><td><Severity value={item.severity}/></td><td>{statusLabel[item.status] || item.status}</td><td><select value={item.status} onChange={e => void changeStatus(item.id, e.target.value)} aria-label={`Ubah status insiden ${item.id}`}><option value="open">Terbuka</option><option value="investigating">Diselidiki</option><option value="resolved">Selesai</option><option value="false_positive">False positive</option></select></td></tr>)}
            {!incidents.length && <tr><td colSpan={5} className="empty-state"><b>Belum ada insiden</b><span>Jalankan simulasi dari halaman ikhtisar.</span></td></tr>}
          </tbody></table></div>
        </section>}

        <AdvancedPanel api={API} />
        <footer className="footer"><div><ShieldCheck size={15}/> <span>SIBERWASPADA AI</span> · Dibuat untuk pertahanan, transparansi, dan pembelajaran.</div><span>Data demo ≠ pemantauan produksi</span></footer>
      </main>
    </div>
  );
}

function StatCard({ icon, label, value, detail, tone }: { icon: React.ReactNode; label: string; value: React.ReactNode; detail: string; tone: string }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}>{icon}</div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{detail}</div></div>;
}

function Severity({ value }: { value: string }) {
  return <span className={`severity severity-${value}`}><span/>{severityLabel[value] || value}</span>;
}

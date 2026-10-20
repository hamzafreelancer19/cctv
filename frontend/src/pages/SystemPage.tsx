import { useEffect, useState } from "react";
import { api, SIEMJob } from "../api/client";
import Icon from "../components/Icon";

export default function SystemPage() {
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [dbUp, setDbUp] = useState<boolean | null>(null);
  const [siem, setSiem] = useState<SIEMJob[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api.getHealth().then((ok) => !cancelled && setApiUp(ok)).catch(() => !cancelled && setApiUp(false));
      api.getReady().then((ok) => !cancelled && setDbUp(ok)).catch(() => !cancelled && setDbUp(false));
      api
        .getSiemJobs()
        .then((data) => !cancelled && setSiem(data.results))
        .catch((e) => !cancelled && setError(e.message));
    };
    load();
    const timer = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const health = (ok: boolean | null) =>
    ok === null ? "…" : ok ? "Operational" : "Down";
  const healthClass = (ok: boolean | null) => (ok === null ? "" : ok ? "online" : "critical");

  return (
    <div>
      <header className="page-header">
        <h1>System &amp; Monitoring</h1>
        <p className="muted">M6.5 – M6.7 · Health probes, Prometheus metrics &amp; SIEM forwarding</p>
      </header>

      <div className="section-title">
        <span className="bar" /> Service Health
      </div>
      <section className="card-grid">
        <div className="stat-card">
          <span className="metric-label">API Gateway</span>
          <span className={`badge ${healthClass(apiUp)}`}>{health(apiUp)}</span>
        </div>
        <div className="stat-card">
          <span className="metric-label">Database (readiness)</span>
          <span className={`badge ${healthClass(dbUp)}`}>{health(dbUp)}</span>
        </div>
        <div className="stat-card">
          <span className="metric-label">Prometheus Metrics</span>
          <a href="/api/v1/metrics/" target="_blank" rel="noreferrer" className="badge info">
            /api/v1/metrics/
          </a>
        </div>
        <div className="stat-card">
          <span className="metric-label">Liveness Probe</span>
          <a href="/api/v1/live/" target="_blank" rel="noreferrer" className="badge info">
            /api/v1/live/
          </a>
        </div>
      </section>

      <div className="section-title">
        <span className="bar" /> SIEM Forwarding
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Target</th>
              <th>Destination</th>
              <th>Attempts</th>
              <th>Status</th>
              <th>Last Error</th>
            </tr>
          </thead>
          <tbody>
            {siem.map((j) => (
              <tr key={j.id}>
                <td>{new Date(j.created_at).toLocaleString()}</td>
                <td style={{ textTransform: "capitalize" }}>{j.target}</td>
                <td>{j.destination}</td>
                <td>
                  {j.attempts}/{j.max_attempts}
                </td>
                <td>
                  <span className={`badge ${j.status}`}>{j.status}</span>
                </td>
                <td className="muted">{j.last_error || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {siem.length === 0 && (
          <div className="empty-state">
            <span className="empty-ic"><Icon name="system" /></span>
            No SIEM forwards yet. Configure targets in organization settings (Splunk, Sentinel, syslog…).
          </div>
        )}
      </div>
    </div>
  );
}

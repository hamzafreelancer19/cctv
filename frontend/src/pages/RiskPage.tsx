import { useEffect, useState } from "react";
import { api, RiskIncident, TimelineItem } from "../api/client";

export default function RiskPage() {
  const [incidents, setIncidents] = useState<RiskIncident[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [inc, tl] = await Promise.all([api.getRiskIncidents(), api.getIncidentTimeline()]);
        if (!cancelled) {
          setIncidents(inc.results);
          setTimeline(tl.results);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed");
      }
    };
    load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  async function act(id: string, action: string) {
    try {
      await api.riskIncidentAction(id, action);
      setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, status: action === "acknowledge" ? "acknowledged" : "resolved" } : i)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    }
  }

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Risk Dashboard</h1>
        <p className="muted">Correlated incidents + timeline</p>
      </header>
      <div className="card-grid">
        {incidents.slice(0, 6).map((i) => (
          <div className="stat-card" key={i.id}>
            <span className={`badge ${i.risk_level}`}>{i.risk_level}</span>
            <strong>{i.title}</strong>
            <p className="muted">
              score {i.risk_score} · {i.event_count} events · {i.status}
            </p>
            {i.status === "open" && (
              <div className="row-actions">
                <button type="button" onClick={() => act(i.id, "acknowledge")}>
                  Ack
                </button>
                <button type="button" onClick={() => act(i.id, "resolve")}>
                  Resolve
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      <h2>Incident Timeline</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Kind</th>
              <th>Title</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((t) => (
              <tr key={`${t.kind}-${t.id}`}>
                <td>{new Date(t.created_at).toLocaleString()}</td>
                <td>{t.kind}</td>
                <td>{t.title}</td>
                <td>
                  <span className={`badge ${t.severity}`}>{t.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

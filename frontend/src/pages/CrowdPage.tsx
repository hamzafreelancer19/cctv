import { useEffect, useState } from "react";
import { api, CrowdSummary, LoiterEvent } from "../api/client";

export default function CrowdPage() {
  const [summary, setSummary] = useState<CrowdSummary | null>(null);
  const [loiters, setLoiters] = useState<LoiterEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const orgs = await api.getOrganizations();
        const orgId = orgs.results[0]?.id;
        const [crowd, loiter] = await Promise.all([
          orgId ? api.getCrowdSummary(orgId) : Promise.resolve(null),
          api.getLoiterEvents(),
        ]);
        if (!cancelled) {
          setSummary(crowd);
          setLoiters(loiter.results);
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

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Crowd Analytics</h1>
        <p className="muted">Occupancy, density, heatmaps, loitering</p>
      </header>
      <div className="card-grid">
        <div className="stat-card">
          <span className="muted">Current</span>
          <strong>{summary?.current_occupancy ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Average today</span>
          <strong>{summary?.average_occupancy ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Peak today</span>
          <strong>{summary?.maximum_occupancy ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Over capacity</span>
          <strong>{summary?.over_capacity ? "Yes" : "No"}</strong>
        </div>
      </div>
      <h2>Heatmap cells</h2>
      <p className="muted">{summary?.heatmap?.length ? `${summary.heatmap.length} active cells` : "No heatmap data yet"}</p>
      <h2>Recent loitering</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Camera</th>
              <th>Zone</th>
              <th>Dwell</th>
              <th>Escalation</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {loiters.map((l) => (
              <tr key={l.id}>
                <td>{new Date(l.created_at).toLocaleString()}</td>
                <td>{l.camera_name}</td>
                <td>{l.zone_name || "—"}</td>
                <td>{l.dwell_seconds.toFixed(0)}s</td>
                <td>{l.escalation_count}</td>
                <td>
                  <span className={`badge ${l.severity}`}>{l.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

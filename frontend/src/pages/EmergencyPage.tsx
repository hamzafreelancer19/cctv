import { useEffect, useMemo, useState } from "react";
import { api, EmergencyIncident, SafetySummary } from "../api/client";
import Icon from "../components/Icon";

function formatAction(action: string): string {
  return action.replace(/_/g, " ");
}

export default function EmergencyPage() {
  const [summary, setSummary] = useState<SafetySummary | null>(null);
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  const load = async () => {
    const [summaryData, incidentData] = await Promise.all([
      api.getSafetySummary(),
      api.getEmergencyIncidents(),
    ]);
    setSummary(summaryData);
    setIncidents(incidentData.results);
  };

  useEffect(() => {
    let cancelled = false;
    const refresh = () =>
      load().catch((cause) => {
        if (!cancelled) setError(cause.message);
      });
    refresh();
    const timer = setInterval(refresh, 4000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const active = useMemo(
    () =>
      incidents.filter((incident) =>
        ["open", "acknowledged", "contained"].includes(incident.status)
      ),
    [incidents]
  );

  async function action(id: string, name: string) {
    setBusyId(id);
    setError("");
    try {
      await api.emergencyIncidentAction(id, name);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Action failed");
    } finally {
      setBusyId("");
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>Emergency Command Center</h1>
        <p className="muted">Unified fire, smoke, weapon, fall, crowd, and PPE response</p>
      </header>
      {error && <div className="error-banner">{error}</div>}
      <div className="card-grid">
        <div className="stat-card"><span className="muted">Open incidents</span><strong>{summary?.incidents_open ?? 0}</strong></div>
        <div className="stat-card"><span className="muted">Emergency</span><strong>{summary?.incidents_emergency ?? 0}</strong></div>
        <div className="stat-card"><span className="muted">Fire today</span><strong>{summary?.fire_today ?? 0}</strong></div>
        <div className="stat-card"><span className="muted">Smoke today</span><strong>{summary?.smoke_today ?? 0}</strong></div>
        <div className="stat-card"><span className="muted">Weapons today</span><strong>{summary?.weapon_today ?? 0}</strong></div>
        <div className="stat-card"><span className="muted">PPE compliance</span><strong>{summary?.ppe_compliance_percent ?? 100}%</strong></div>
      </div>

      <div className="section-title">
        <span className="bar" /> Active Incidents
      </div>

      {active.length === 0 ? (
        <div className="empty-state panel">
          <span className="empty-ic"><Icon name="emergency" /></span>
          No active emergencies — all clear
        </div>
      ) : (
        <div className="card-grid">
          {active.map((incident) => (
            <div className={`alert-card emergency-card ${incident.severity}`} key={incident.id}>
              <div className="alert-card-body">
                <div className="alert-header">
                  <strong>{incident.title}</strong>
                  <span className={`badge ${incident.severity}`}>{incident.severity}</span>
                </div>
                <p>{incident.summary}</p>
                <p className="muted">
                  {incident.site_name || "Unknown site"}
                  {incident.camera_name ? ` · ${incident.camera_name}` : ""}
                  {" · "}score {Math.round(incident.score)}
                  {" · "}{incident.event_count} events
                  {" · "}{incident.status}
                </p>
                {incident.recommended_actions.length > 0 && (
                  <div className="chip-row">
                    {incident.recommended_actions.map((item) => (
                      <span className="chip" key={item}>{formatAction(item)}</span>
                    ))}
                  </div>
                )}
                <div className="row-actions">
                  {incident.status === "open" && (
                    <button type="button" disabled={busyId === incident.id} onClick={() => action(incident.id, "acknowledge")}>
                      Acknowledge
                    </button>
                  )}
                  {["open", "acknowledged"].includes(incident.status) && (
                    <button type="button" disabled={busyId === incident.id} onClick={() => action(incident.id, "contain")}>
                      Contain
                    </button>
                  )}
                  <button type="button" disabled={busyId === incident.id} onClick={() => action(incident.id, "resolve")}>
                    Resolve
                  </button>
                  <button type="button" disabled={busyId === incident.id} onClick={() => action(incident.id, "false_positive")}>
                    False positive
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

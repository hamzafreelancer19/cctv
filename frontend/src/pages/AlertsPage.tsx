import { useCallback, useEffect, useMemo, useState } from "react";
import { api, Alert } from "../api/client";
import Icon from "../components/Icon";

type AlertStatusFilter = "all" | "open" | "acknowledged";

function formatEventType(value: string) {
  return (value || "security event")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character: string) => character.toUpperCase());
}

/** Old alerts used "Unknown Person — hamza" where hamza is the camera, not a person. */
function displayAlertTitle(alert: Alert) {
  let title = (alert.title || "").trim();
  const camera = (alert.camera_name || "").trim();
  if (camera) {
    const suffix = ` — ${camera}`;
    if (title.endsWith(suffix)) {
      title = title.slice(0, -suffix.length).trim();
    }
  }
  return title || formatEventType(alert.event_type);
}

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [acknowledgingId, setAcknowledgingId] = useState("");
  const [statusFilter, setStatusFilter] = useState<AlertStatusFilter>("open");

  const loadAlerts = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    try {
      const data = await api.getAlerts();
      setAlerts(data.results);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load alerts");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      if (active) await loadAlerts(true);
    };
    refresh();
    const timer = window.setInterval(refresh, 4000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [loadAlerts]);

  async function handleAck(id: string) {
    setAcknowledgingId(id);
    try {
      const updated = await api.acknowledgeAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Acknowledge failed");
    } finally {
      setAcknowledgingId("");
    }
  }

  const filteredAlerts = useMemo(() => {
    return alerts.filter(
      (alert) => statusFilter === "all" || alert.status === statusFilter
    );
  }, [alerts, statusFilter]);

  return (
    <div className="alerts-page">
      <header className="page-header alerts-page-header">
        <div>
          <h1>Security Alerts</h1>
        </div>
        <button className="btn secondary alert-refresh" onClick={() => loadAlerts()} disabled={refreshing}>
          <Icon name="event" />
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {error && <div className="error-banner alert-page-error">{error}</div>}

      <div className="alert-controls">
        <div className="alert-status-tabs">
          {(["open", "acknowledged", "all"] as AlertStatusFilter[]).map((status) => (
            <button
              key={status}
              className={statusFilter === status ? "active" : ""}
              onClick={() => setStatusFilter(status)}
            >
              {status === "all" ? "All" : status === "open" ? "Open" : "Done"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="alert-loading-grid">
          {[1, 2, 3].map((item) => (
            <div className="skeleton" key={item} />
          ))}
        </div>
      ) : (
        <div className="alert-list">
          {filteredAlerts.map((alert) => (
            <article key={alert.id} className={`alert-card ${alert.severity}`}>
              <div className={`alert-severity-icon ${alert.severity}`}>
                <Icon name={alert.severity === "critical" ? "alert" : "bell"} />
              </div>
              <div className="alert-card-body">
                <div className="alert-header">
                  <div>
                    <div className="alert-title-row">
                      <span className={`badge ${alert.severity}`}>{alert.severity}</span>
                    </div>
                    <h3>{displayAlertTitle(alert)}</h3>
                  </div>
                  <span title={new Date(alert.created_at).toLocaleString()}>
                    {relativeTime(alert.created_at)}
                  </span>
                </div>
                {alert.message && <p className="alert-message">{alert.message}</p>}
                <div className="alert-meta">
                  <span className="alert-location">
                    <Icon name="camera" />
                    {alert.camera_name || "Camera"}
                    {alert.site_name ? ` · ${alert.site_name}` : ""}
                  </span>
                </div>
                {alert.status === "open" && (
                  <button
                    className="alert-ack-btn"
                    onClick={() => handleAck(alert.id)}
                    disabled={acknowledgingId === alert.id}
                  >
                    {acknowledgingId === alert.id ? "Acknowledging…" : "Acknowledge"}
                  </button>
                )}
              </div>
            </article>
          ))}
          {filteredAlerts.length === 0 && (
            <div className="empty-state alert-empty-state">
              <span className="empty-ic">
                <Icon name="bell" />
              </span>
              <h3>{alerts.length === 0 ? "No alerts" : "No alerts here"}</h3>
              <p>
                {alerts.length === 0
                  ? "New camera alerts will show up here."
                  : "Try another tab."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

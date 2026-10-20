import { useEffect, useState } from "react";
import { api, DetectionEvent } from "../api/client";
import Icon from "../components/Icon";

export default function EventsPage() {
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [error, setError] = useState("");
  const [deletingAll, setDeletingAll] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getEvents()
        .then((data) => {
          if (!cancelled) setEvents(data.results);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        });
    load();
    const timer = setInterval(load, 4000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  async function handleReview(id: string, status: string) {
    try {
      await api.reviewEvent(id, status);
      setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, review_status: status } : e)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed");
    }
  }

  async function deleteAll() {
    if (!window.confirm("Delete all events and linked alert records? This cannot be undone.")) return;
    setDeletingAll(true);
    try {
      await api.deleteAllEvents();
      setEvents([]);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingAll(false);
    }
  }

  return (
    <div>
      <header className="page-header events-page-header">
        <div>
          <h1>Event Review Queue</h1>
          <p className="muted">M2 detections (person / intrusion / activity) — auto-refresh 4s</p>
        </div>
        <button
          className="btn data-delete-all"
          onClick={deleteAll}
          disabled={events.length === 0 || deletingAll}
        >
          <Icon name="trash" />
          {deletingAll ? "Deleting…" : "Delete all"}
        </button>
      </header>
      {error && <div className="error-banner">{error}</div>}
      {events.length === 0 ? (
        <div className="empty-state">
          <span className="empty-ic"><Icon name="event" /></span>
          <h3>No events yet</h3>
          <p>Detections from live cameras will appear here automatically.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Camera</th>
                <th>Site</th>
                <th>Track</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id}>
                  <td>{new Date(ev.created_at).toLocaleString()}</td>
                  <td>{ev.event_type.replace(/_/g, " ")}</td>
                  <td>{ev.camera_name}</td>
                  <td>{ev.site_name}</td>
                  <td>{String(ev.payload?.track_id ?? "—")}</td>
                  <td>
                    <span className={`badge ${ev.severity}`}>{ev.severity}</span>
                  </td>
                  <td>{(ev.confidence * 100).toFixed(0)}%</td>
                  <td>{ev.review_status}</td>
                  <td className="actions">
                    {ev.review_status === "pending" && (
                      <>
                        <button onClick={() => handleReview(ev.id, "confirmed")}>Confirm</button>
                        <button className="secondary" onClick={() => handleReview(ev.id, "false_positive")}>
                          False+
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

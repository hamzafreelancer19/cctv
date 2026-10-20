import { useEffect, useState } from "react";
import { api, NotificationJob } from "../api/client";
import Icon from "../components/Icon";

const channelLabels: Record<string, string> = {
  email: "Email",
  sms: "SMS",
  whatsapp: "WhatsApp",
  push: "Push",
  webhook: "Webhook",
};

export default function NotificationsPage() {
  const [jobs, setJobs] = useState<NotificationJob[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getNotifications()
        .then((data) => !cancelled && setJobs(data.results))
        .catch((e) => !cancelled && setError(e.message));
    load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const counts = jobs.reduce(
    (acc, j) => {
      acc.total += 1;
      if (j.status === "sent") acc.sent += 1;
      else if (j.status === "dead") acc.dead += 1;
      else if (j.status === "failed") acc.failed += 1;
      else acc.queued += 1;
      return acc;
    },
    { total: 0, sent: 0, failed: 0, dead: 0, queued: 0 }
  );

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Notification Delivery</h1>
        <p className="muted">M6.1 · Celery workers with retry, dead-letter &amp; rate limiting — auto-refresh 5s</p>
      </header>

      <section className="metric-grid">
        <div className="metric-card">
          <span className="metric-value">{counts.total}</span>
          <span className="metric-label">Total Jobs</span>
        </div>
        <div className="metric-card success">
          <span className="metric-value">{counts.sent}</span>
          <span className="metric-label">Delivered</span>
        </div>
        <div className="metric-card warning">
          <span className="metric-value">{counts.queued}</span>
          <span className="metric-label">Queued</span>
        </div>
        <div className="metric-card warning">
          <span className="metric-value">{counts.failed}</span>
          <span className="metric-label">Retrying</span>
        </div>
        <div className="metric-card critical">
          <span className="metric-value">{counts.dead}</span>
          <span className="metric-label">Dead Letter</span>
        </div>
      </section>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Channel</th>
              <th>Destination</th>
              <th>Subject</th>
              <th>Attempts</th>
              <th>Status</th>
              <th>Last Error</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>{new Date(j.created_at).toLocaleString()}</td>
                <td>{channelLabels[j.channel] || j.channel}</td>
                <td>{j.destination || "—"}</td>
                <td>{j.subject || "—"}</td>
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
        {jobs.length === 0 && (
          <div className="empty-state">
            <span className="empty-ic"><Icon name="bell" /></span>
            No notification jobs yet. Critical events auto-enqueue deliveries.
          </div>
        )}
      </div>
    </div>
  );
}

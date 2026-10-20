import { useEffect, useState } from "react";
import { api, DashboardSummary } from "../api/client";
import Icon from "../components/Icon";

function MetricCard({
  label,
  value,
  accent,
  icon,
}: {
  label: string;
  value: number | string;
  accent?: string;
  icon: string;
}) {
  return (
    <article className={`metric-card ${accent || ""}`}>
      <div className="metric-top">
        <span className="metric-ic">
          <Icon name={icon} className="nav-icon" />
        </span>
      </div>
      <span className="metric-value">{value}</span>
      <span className="metric-label">{label}</span>
    </article>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .getDashboardSummary()
        .then((s) => {
          if (cancelled) return;
          setSummary(s);
          setUpdatedAt(new Date().toLocaleTimeString());
        })
        .catch((e) => !cancelled && setError(e.message));
    };
    load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!summary)
    return (
      <div className="metric-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 120 }} />
        ))}
      </div>
    );

  return (
    <div>
      <header className="page-header">
        <h1>Dashboard</h1>
        <p className="muted">
          Live status{updatedAt ? ` · updated ${updatedAt}` : ""}
        </p>
      </header>

      <section className="metric-grid">
        <MetricCard
          label="Cameras Online"
          value={`${summary.cameras_online}/${summary.cameras_total}`}
          icon="camera"
          accent="success"
        />
        <MetricCard label="Events Today" value={summary.events_today} icon="event" />
        <MetricCard
          label="Open Alerts"
          value={summary.alerts_open}
          accent="warning"
          icon="bell"
        />
        <MetricCard
          label="Critical Alerts"
          value={summary.alerts_critical}
          accent="critical"
          icon="alert"
        />
      </section>
    </div>
  );
}

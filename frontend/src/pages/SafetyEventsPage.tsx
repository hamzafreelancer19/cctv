import { useEffect, useState } from "react";
import { api, SafetyEvent } from "../api/client";

type SafetyKind = "fire" | "smoke" | "weapon" | "fall" | "ppe";

const TITLES: Record<SafetyKind, string> = {
  fire: "Fire Monitoring",
  smoke: "Smoke Monitoring",
  weapon: "Weapon Alerts",
  fall: "Fall Detection",
  ppe: "PPE Compliance",
};

function detail(kind: SafetyKind, event: SafetyEvent) {
  if (kind === "fire") return `${event.environment || "indoor"} · ${event.verified ? "verified" : "unverified"}`;
  if (kind === "smoke") return `${event.density_level || "low"} density · ${event.trend || "stable"}${event.persistent ? " · persistent" : ""}`;
  if (kind === "weapon") return `${event.weapon_type || "unknown"} · track ${event.track_id ?? "—"}${event.person_name ? ` · ${event.person_name}` : ""}`;
  if (kind === "fall") return `${event.status || "fallen"} · immobile ${Math.round(event.immobile_seconds || 0)}s`;
  return `${event.compliant ? "Compliant" : `Missing ${(event.missing_items || []).join(", ")}`} · ${event.person_type || "all roles"}`;
}

export default function SafetyEventsPage({ kind }: { kind: SafetyKind }) {
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getSafetyEvents(kind)
        .then((response) => {
          if (!cancelled) setEvents(response.results);
        })
        .catch((cause) => {
          if (!cancelled) setError(cause.message);
        });
    load();
    const timer = setInterval(load, 4000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [kind]);

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>{TITLES[kind]}</h1>
        <p className="muted">Verified M5 life-safety events · auto-refresh 4s</p>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Camera</th>
              <th>Zone</th>
              <th>Confidence</th>
              <th>Duration</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td>{new Date(event.created_at).toLocaleString()}</td>
                <td>{event.camera_name}</td>
                <td>{event.zone_name || "—"}</td>
                <td>{(event.confidence * 100).toFixed(0)}%</td>
                <td>{Math.round(event.duration_seconds || 0)}s</td>
                <td>{detail(kind, event)}</td>
              </tr>
            ))}
            {!events.length && (
              <tr>
                <td colSpan={6} className="muted">No {kind} events recorded.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api, ZoneInfo } from "../api/client";

export default function ZonesPage() {
  const [zones, setZones] = useState<ZoneInfo[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getZones()
        .then((data) => {
          if (!cancelled) setZones(data.results);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        });
    load();
    const timer = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Zone Monitoring</h1>
        <p className="muted">Multi-zone intrusion, priority, schedules, dwell timers</p>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Site</th>
              <th>Priority</th>
              <th>Restricted</th>
              <th>Loiter (s)</th>
              <th>Max Occ.</th>
              <th>Hours</th>
            </tr>
          </thead>
          <tbody>
            {zones.map((z) => (
              <tr key={z.id}>
                <td>{z.name}</td>
                <td>{z.site_name}</td>
                <td>
                  <span className={`badge ${z.priority}`}>{z.priority}</span>
                </td>
                <td>{z.is_restricted ? "Yes" : "No"}</td>
                <td>{z.loitering_seconds}</td>
                <td>{z.max_occupancy ?? "—"}</td>
                <td>
                  {z.access_start && z.access_end ? `${z.access_start}–${z.access_end}` : "Always"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

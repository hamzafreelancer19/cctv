import { useEffect, useState } from "react";
import { api, ObjectEvent } from "../api/client";

export default function ObjectsPage() {
  const [items, setItems] = useState<ObjectEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getObjectEvents()
        .then((data) => {
          if (!cancelled) setItems(data.results);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        });
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
        <h1>Object Monitoring</h1>
        <p className="muted">Bags left behind, equipment removed, abandoned packages</p>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Kind</th>
              <th>Object</th>
              <th>Camera</th>
              <th>Dwell</th>
              <th>Confidence</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {items.map((o) => (
              <tr key={o.id}>
                <td>{new Date(o.created_at).toLocaleString()}</td>
                <td>{o.kind}</td>
                <td>{o.object_class}</td>
                <td>{o.camera_name}</td>
                <td>{o.dwell_seconds.toFixed(0)}s</td>
                <td>{(o.confidence * 100).toFixed(0)}%</td>
                <td>
                  <span className={`badge ${o.severity}`}>{o.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

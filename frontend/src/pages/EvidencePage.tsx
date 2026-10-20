import { useEffect, useState } from "react";
import { api, SnapshotObject } from "../api/client";
import Icon from "../components/Icon";

function formatBytes(n: number): string {
  if (!n) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(1)} ${units[i]}`;
}

export default function EvidencePage() {
  const [items, setItems] = useState<SnapshotObject[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .getSnapshots()
        .then((data) => !cancelled && setItems(data.results))
        .catch((e) => !cancelled && setError(e.message));
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
        <h1>Evidence Store</h1>
        <p className="muted">M6.2 · Signed snapshot evidence on local / MinIO / S3 with integrity metadata</p>
      </header>

      <div className="card-grid">
        {items.map((s) => (
          <article key={s.id} className="stat-card" style={{ padding: 0, overflow: "hidden" }}>
            <a href={s.snapshot_url} target="_blank" rel="noreferrer">
              <img
                src={s.thumbnail_url || s.snapshot_url}
                alt={s.snapshot_key}
                style={{ width: "100%", height: 150, objectFit: "cover", background: "var(--surface-2)" }}
                onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
              />
            </a>
            <div style={{ padding: "0.9rem 1rem", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
              <strong style={{ fontSize: "0.9rem" }}>{s.camera_name}</strong>
              <div className="muted" style={{ fontSize: "0.78rem" }}>
                {s.width && s.height ? `${s.width}×${s.height} · ` : ""}
                {formatBytes(s.size_bytes)}
              </div>
              <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                <span className="badge">{s.storage_backend}</span>
                {s.uploaded_by_edge && <span className="badge info">edge</span>}
              </div>
              <div className="muted" style={{ fontSize: "0.72rem" }}>
                {new Date(s.created_at).toLocaleString()}
              </div>
              {s.checksum && (
                <div className="muted" style={{ fontSize: "0.68rem", wordBreak: "break-all" }}>
                  sha256: {s.checksum.slice(0, 16)}…
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
      {items.length === 0 && (
        <div className="empty-state">
          <span className="empty-ic"><Icon name="evidence" /></span>
          No evidence stored yet. Edge uploads populate this gallery with signed URLs.
        </div>
      )}
    </div>
  );
}

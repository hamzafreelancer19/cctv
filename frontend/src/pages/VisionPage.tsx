import { useEffect, useState } from "react";
import { api, VisionCapture } from "../api/client";
import Icon from "../components/Icon";

export default function VisionPage() {
  const [captures, setCaptures] = useState<VisionCapture[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [deletingAll, setDeletingAll] = useState(false);
  const [selected, setSelected] = useState<VisionCapture | null>(null);

  async function load() {
    try {
      const captureData = await api.getVisionCaptures();
      setCaptures(captureData.results);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load vision captures");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 8000);
    return () => window.clearInterval(timer);
  }, []);

  async function deleteAll() {
    if (!window.confirm("Delete all AI Vision captures and their images? This cannot be undone.")) return;
    setDeletingAll(true);
    try {
      await api.deleteAllVisionCaptures();
      setCaptures([]);
      setSelected(null);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingAll(false);
    }
  }

  return (
    <div className="vision-page">
      <div className="vision-page-actions">
        <button
          className="btn data-delete-all"
          onClick={deleteAll}
          disabled={captures.length === 0 || deletingAll}
        >
          <Icon name="trash" />
          {deletingAll ? "Deleting…" : "Delete all"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="vision-gallery">
          {[1, 2, 3].map((item) => (
            <div key={item} className="vision-card skeleton" />
          ))}
        </div>
      ) : (
        <div className="vision-gallery">
          {captures.length === 0 && (
            <div className="empty-state" style={{ gridColumn: "1 / -1" }}>
              <span className="empty-ic"><Icon name="vision" /></span>
              No activity captures yet. AI only saves when a real person/threat is detected —
              empty rooms and random objects are ignored.
            </div>
          )}
          {captures.map((capture) => (
            <article key={capture.id} className="vision-card">
              <button
                className="vision-image"
                onClick={() => setSelected(capture)}
                disabled={!capture.image_url}
              >
                {capture.image_url ? (
                  <img src={capture.image_url} alt={capture.summary} />
                ) : (
                  <span className="vision-image-placeholder">
                    <Icon name="vision" />
                    No image
                  </span>
                )}
              </button>
              <div className="vision-card-body">
                <div className="vision-card-top">
                  <strong>{capture.camera_name}</strong>
                  <span>{new Date(capture.created_at).toLocaleString()}</span>
                </div>
                <p>{capture.summary}</p>
                <div className="vision-tags">
                  {(capture.people || []).length > 0 && (
                    <span className="chip">{capture.people.length} unknown</span>
                  )}
                  {(capture.people || []).slice(0, 3).map((person, index) => (
                    <span key={index} className="chip">
                      {person.description || person.activity || "person"}
                    </span>
                  ))}
                </div>
                {(capture.risks || []).length > 0 && (
                  <div className="vision-risks">
                    {capture.risks.slice(0, 2).map((risk, index) => (
                      <span key={index} className={`badge ${risk.level || "warning"}`}>
                        {risk.detail || risk.level || "risk"}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </article>
          ))}

          {captures.length === 0 && (
            <div className="empty-state vision-empty">
              <span className="empty-ic">
                <Icon name="vision" />
              </span>
              <h3>No unknown people yet</h3>
              <p>Only unknown humans are saved here — enrolled faces and random objects are skipped.</p>
            </div>
          )}
        </div>
      )}

      {selected && (
        <div className="unknown-lightbox" role="dialog" aria-modal="true" onClick={() => setSelected(null)}>
          <div className="unknown-lightbox-content vision-lightbox" onClick={(e) => e.stopPropagation()}>
            <button className="unknown-lightbox-close" onClick={() => setSelected(null)} aria-label="Close">
              ×
            </button>
            {selected.image_url && <img src={selected.image_url} alt={selected.summary} />}
            <div className="vision-detail">
              <h3>{selected.camera_name}</h3>
              <p>{selected.summary}</p>
              {selected.scene && <p className="muted">Scene: {selected.scene}</p>}
              {(selected.people || []).length > 0 && (
                <div>
                  <strong>People</strong>
                  <ul>
                    {selected.people.map((person, index) => (
                      <li key={index}>
                        {person.description || "Person"}
                        {person.activity ? ` — ${person.activity}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(selected.detected_objects || []).length > 0 && (
                <div>
                  <strong>Objects</strong>
                  <ul>
                    {selected.detected_objects.map((object, index) => (
                      <li key={index}>
                        {object.name || "Object"}
                        {object.detail ? ` — ${object.detail}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="muted small">
                {selected.provider} · {selected.model_name} ·{" "}
                {Math.round(selected.confidence * 100)}% confidence
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

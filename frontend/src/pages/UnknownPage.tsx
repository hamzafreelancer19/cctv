import { useEffect, useMemo, useState } from "react";
import { api, UnknownSighting } from "../api/client";
import Icon from "../components/Icon";

export default function UnknownPage() {
  const [items, setItems] = useState<UnknownSighting[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"open" | "reviewed" | "all">("open");
  const [reviewingId, setReviewingId] = useState("");
  const [deletingAll, setDeletingAll] = useState(false);
  const [selected, setSelected] = useState<UnknownSighting | null>(null);

  async function load() {
    try {
      const data = await api.getUnknownSightings();
      setItems(data.results);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  async function review(id: string) {
    setReviewingId(id);
    try {
      await api.reviewUnknown(id, true);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed");
    } finally {
      setReviewingId("");
    }
  }

  async function deleteAll() {
    if (!window.confirm("Delete all unknown person images? This cannot be undone.")) return;
    setDeletingAll(true);
    try {
      await api.deleteAllUnknownSightings();
      setItems([]);
      setSelected(null);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingAll(false);
    }
  }

  const visibleItems = useMemo(
    () =>
      items.filter(
        (item) =>
          filter === "all" || (filter === "reviewed" ? item.reviewed : !item.reviewed)
      ),
    [filter, items]
  );

  return (
    <div className="unknown-page">
      <header className="page-header unknown-page-header">
        <div>
          <h1>Unknown Persons</h1>
        </div>
        <div className="unknown-header-actions">
          <button
            className="btn unknown-delete-all"
            onClick={deleteAll}
            disabled={items.length === 0 || deletingAll}
          >
            <Icon name="trash" />
            {deletingAll ? "Deleting…" : "Delete all"}
          </button>
        </div>
      </header>

      {error && <div className="error-banner unknown-error">{error}</div>}

      <div className="unknown-toolbar">
        <div className="alert-status-tabs">
          {(["open", "reviewed", "all"] as const).map((value) => (
            <button
              key={value}
              className={filter === value ? "active" : ""}
              onClick={() => setFilter(value)}
            >
              {value === "open" ? "New" : value === "reviewed" ? "Reviewed" : "All"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="unknown-gallery">
          {[1, 2, 3].map((item) => (
            <div key={item} className="unknown-card skeleton" />
          ))}
        </div>
      ) : (
        <div className="unknown-gallery">
          {visibleItems.map((sighting) => (
            <article
              key={sighting.id}
              className={`unknown-card ${sighting.reviewed ? "reviewed" : ""}`}
            >
              <button
                className="unknown-image"
                onClick={() => sighting.snapshot_url && setSelected(sighting)}
                disabled={!sighting.snapshot_url}
                title={sighting.snapshot_url ? "Open full image" : "Snapshot unavailable"}
              >
                {sighting.snapshot_url ? (
                  <img
                    src={sighting.snapshot_url}
                    alt={`Unknown person from ${sighting.camera_name || "camera"}`}
                  />
                ) : (
                  <span className="unknown-image-placeholder">
                    <Icon name="unknown" />
                    No image
                  </span>
                )}
              </button>

              <div className="unknown-card-body">
                <div className="unknown-location">
                  <Icon name="camera" />
                  <span>{sighting.camera_name || "Camera"}</span>
                  <span>·</span>
                  <span>
                    {new Date(sighting.created_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                {!sighting.reviewed && (
                  <button
                    className="btn unknown-review-btn"
                    onClick={() => review(sighting.id)}
                    disabled={reviewingId === sighting.id}
                  >
                    {reviewingId === sighting.id ? "Saving…" : "Mark reviewed"}
                  </button>
                )}
              </div>
            </article>
          ))}

          {visibleItems.length === 0 && (
            <div className="empty-state unknown-empty">
              <span className="empty-ic">
                <Icon name="unknown" />
              </span>
              <h3>{items.length === 0 ? "No unknown persons" : "Nothing here"}</h3>
              <p>
                {items.length === 0
                  ? "Unrecognized people from live cameras show up here."
                  : "Try another tab."}
              </p>
            </div>
          )}
        </div>
      )}

      {selected?.snapshot_url && (
        <div
          className="unknown-lightbox"
          role="dialog"
          aria-modal="true"
          onClick={() => setSelected(null)}
        >
          <div className="unknown-lightbox-content" onClick={(event) => event.stopPropagation()}>
            <button
              className="unknown-lightbox-close"
              onClick={() => setSelected(null)}
              aria-label="Close"
            >
              ×
            </button>
            <img src={selected.snapshot_url} alt="Unknown person full view" />
            <div>
              <strong>{selected.camera_name || "Camera"}</strong>
              <span>{new Date(selected.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

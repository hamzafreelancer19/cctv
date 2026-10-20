import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Person, PersonSighting } from "../api/client";
import Icon from "../components/Icon";

const PERSON_TYPES = [
  ["student", "Student"],
  ["internship", "Internship"],
  ["junior", "Junior"],
  ["senior", "Senior"],
  ["teacher", "Teacher"],
  ["manager", "Manager"],
  ["ceo", "CEO"],
  ["staff", "Staff"],
  ["visitor", "Visitor"],
  ["blacklist", "Blacklist / Thief"],
] as const;

export default function PersonsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [persons, setPersons] = useState<Person[]>([]);
  const [sightings, setSightings] = useState<PersonSighting[]>([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("selected") || "");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [selectedSighting, setSelectedSighting] = useState<PersonSighting | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("student");
  const [editDepartment, setEditDepartment] = useState("");
  const [editWatchMobile, setEditWatchMobile] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);

  async function load() {
    try {
      const data = await api.getPersons();
      setPersons(data.results.filter((person) => person.person_type !== "unknown"));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  async function loadSightings(personId: string) {
    if (!personId) {
      setSightings([]);
      return;
    }
    try {
      const data = await api.getPersonSightings(personId);
      setSightings(data.results);
    } catch {
      setSightings([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const fromUrl = searchParams.get("selected") || "";
    if (fromUrl && fromUrl !== selectedId) {
      setSelectedId(fromUrl);
    }
  }, [searchParams]);

  useEffect(() => {
    setSelectedSighting(null);
    setEditingProfile(false);
    loadSightings(selectedId);
    if (!selectedId) return;
    const timer = window.setInterval(() => loadSightings(selectedId), 5000);
    return () => window.clearInterval(timer);
  }, [selectedId]);

  useEffect(() => {
    const person = persons.find((p) => p.id === selectedId);
    if (!person) return;
    setEditName(person.full_name);
    setEditType(person.person_type);
    setEditDepartment(person.department || "");
    setEditWatchMobile(Boolean(person.watch_mobile_activity));
  }, [selectedId, persons]);

  function selectPerson(id: string) {
    setSelectedId(id);
    setSearchParams(id ? { selected: id } : {});
  }

  async function handleDelete(person: Person) {
    if (!window.confirm(`Remove ${person.full_name}?`)) return;
    try {
      await api.deletePerson(person.id);
      if (selectedId === person.id) {
        selectPerson("");
        setSightings([]);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleDeleteSighting(sighting: PersonSighting) {
    if (!window.confirm("Delete this log image?")) return;
    try {
      await api.deletePersonSighting(sighting.id);
      setSightings((current) => current.filter((item) => item.id !== sighting.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  function openEditProfile() {
    if (!selected) return;
    setEditName(selected.full_name);
    setEditType(selected.person_type);
    setEditDepartment(selected.department || "");
    setEditWatchMobile(Boolean(selected.watch_mobile_activity));
    setEditingProfile(true);
  }

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setProfileSaving(true);
    setError("");
    try {
      const updated = await api.updatePerson(selected.id, {
        full_name: editName.trim(),
        person_type: editType,
        department: editDepartment.trim(),
        watch_mobile_activity: editWatchMobile,
      });
      setPersons((current) => current.map((p) => (p.id === updated.id ? { ...p, ...updated } : p)));
      setEditingProfile(false);
      setMessage(
        editWatchMobile
          ? `${updated.full_name}: profile saved · strict mobile watch ON`
          : `${updated.full_name}: profile saved`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile");
    } finally {
      setProfileSaving(false);
    }
  }

  async function toggleWatchMobile() {
    if (!selected) return;
    const next = !Boolean(selected.watch_mobile_activity);
    setProfileSaving(true);
    setError("");
    try {
      const updated = await api.updatePerson(selected.id, { watch_mobile_activity: next });
      setPersons((current) => current.map((p) => (p.id === updated.id ? { ...p, ...updated } : p)));
      setEditWatchMobile(next);
      setMessage(
        next
          ? `Strict watch ON for ${updated.full_name} — cameras will log their mobile use`
          : `Strict watch OFF for ${updated.full_name}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update watch setting");
    } finally {
      setProfileSaving(false);
    }
  }

  const selected = persons.find((person) => person.id === selectedId) || null;

  return (
    <div>
      <header className="page-header persons-page-header">
        <div>
          <h1>People</h1>
          <p className="muted">Saved profiles — open one to view logs or edit.</p>
        </div>
        <Link to="/persons/new" className="btn">
          <Icon name="people" />
          Enroll Person
        </Link>
      </header>

      {error && <div className="error-banner">{error}</div>}
      {message && <p className="muted">{message}</p>}

      <div className="people-grid people-profiles-grid">
        {persons.length === 0 && (
          <div className="empty-state">
            <Icon name="people" />
            <h3>No profiles yet</h3>
            <p>Add a person to start face enrollment.</p>
            <Link to="/persons/new" className="btn">
              Enroll Person
            </Link>
          </div>
        )}
        {persons.map((p) => (
          <article
            key={p.id}
            className={`person-card ${selectedId === p.id ? "selected" : ""}`}
            onClick={() => selectPerson(p.id)}
          >
            <div className="person-avatar">
              {p.primary_image_url ? (
                <img
                  src={`${p.primary_image_url}${p.primary_image_url.includes("?") ? "&" : "?"}v=${p.id}`}
                  alt={p.full_name}
                />
              ) : (
                <Icon name="people" />
              )}
            </div>
            <div className="person-info">
              <strong>{p.full_name}</strong>
              <span className={`chip ${p.person_type}`}>{p.person_type}</span>
              {p.watch_mobile_activity && <span className="chip watch-on">Strict watch</span>}
              {p.department && <span className="muted small">{p.department}</span>}
              <span className="muted small">
                {p.embedding_count >= 5
                  ? `Ready · ${p.embedding_count} scans`
                  : p.embedding_count > 0
                    ? `Partial · ${p.embedding_count}/5 angles`
                    : "No face scan yet"}
              </span>
            </div>
            <button
              className="icon-btn"
              title="Remove"
              onClick={(event) => {
                event.stopPropagation();
                handleDelete(p);
              }}
            >
              <Icon name="trash" />
            </button>
          </article>
        ))}
      </div>

      {selected && (
        <section className="person-profile-logs">
          <header>
            <div className="person-profile-identity">
              <div className="person-profile-avatar">
                {selected.primary_image_url ? (
                  <img src={selected.primary_image_url} alt={selected.full_name} />
                ) : (
                  <Icon name="people" />
                )}
              </div>
              <div>
                <h2>{selected.full_name}</h2>
                <p>
                  <span className={`chip ${selected.person_type}`}>{selected.person_type}</span>
                  {selected.watch_mobile_activity && (
                    <span className="chip watch-on">Strict mobile watch</span>
                  )}
                  <span className="muted small">
                    {sightings.length === 0
                      ? "No camera activity yet"
                      : `${sightings.length} camera log${sightings.length === 1 ? "" : "s"}`}
                  </span>
                </p>
              </div>
            </div>
            <div className="person-profile-actions">
              <button
                type="button"
                className={`btn secondary ${selected.watch_mobile_activity ? "watch-active" : ""}`}
                onClick={toggleWatchMobile}
                disabled={profileSaving}
                title="Only this person — cameras log mobile use activity"
              >
                {selected.watch_mobile_activity ? "Strict watch ON" : "Strict mobile watch"}
              </button>
              <button type="button" className="btn" onClick={openEditProfile} disabled={profileSaving}>
                Edit profile
              </button>
            </div>
          </header>

          {editingProfile && (
            <form className="person-edit-form" onSubmit={saveProfile}>
              <label>
                Full name
                <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
              </label>
              <label>
                Type
                <select value={editType} onChange={(e) => setEditType(e.target.value)}>
                  {PERSON_TYPES.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                  {!PERSON_TYPES.some(([value]) => value === editType) && (
                    <option value={editType}>{editType}</option>
                  )}
                </select>
              </label>
              <label>
                Department (optional)
                <input
                  value={editDepartment}
                  onChange={(e) => setEditDepartment(e.target.value)}
                />
              </label>
              <label className="check-option person-watch-option">
                <input
                  type="checkbox"
                  checked={editWatchMobile}
                  onChange={(e) => setEditWatchMobile(e.target.checked)}
                />
                <span>
                  Strict mobile watch — cameras only track <em>this</em> person&apos;s mobile use
                  and save that activity here
                </span>
              </label>
              <div className="person-edit-actions">
                <button type="button" className="btn secondary" onClick={() => setEditingProfile(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn" disabled={profileSaving || !editName.trim()}>
                  {profileSaving ? "Saving…" : "Save profile"}
                </button>
              </div>
            </form>
          )}

          {sightings.length === 0 ? (
            <div className="empty-state person-logs-empty">
              <span className="empty-ic">
                <Icon name="camera" />
              </span>
              <h3>No camera logs yet</h3>
              <p>
                {selected.watch_mobile_activity
                  ? "Strict watch is ON — when this person uses a mobile on camera, activity will show here."
                  : "Turn on Strict mobile watch to log only this person’s mobile activity on cameras."}
              </p>
            </div>
          ) : (
            <div className="person-sighting-grid">
              {sightings.map((sighting) => {
                const onMobile = sighting.notes === "mobile_in_use";
                return (
                  <article key={sighting.id} className="person-sighting-card">
                    <button
                      type="button"
                      className="person-sighting-image"
                      onClick={() => sighting.snapshot_url && setSelectedSighting(sighting)}
                      disabled={!sighting.snapshot_url}
                    >
                      {sighting.snapshot_url ? (
                        <img
                          src={sighting.snapshot_url}
                          alt={`${selected.full_name} on camera`}
                        />
                      ) : (
                        <span className="muted">No image</span>
                      )}
                      {onMobile && <span className="person-sighting-tag">Mobile</span>}
                    </button>
                    <div className="person-sighting-meta">
                      <div>
                        <strong>{sighting.camera_name || "Camera"}</strong>
                        <span className="muted small">
                          {new Date(sighting.created_at).toLocaleString([], {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <button
                        type="button"
                        className="icon-btn"
                        title="Delete"
                        aria-label="Delete log"
                        onClick={() => handleDeleteSighting(sighting)}
                      >
                        <Icon name="trash" />
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}

      {selectedSighting?.snapshot_url && (
        <div
          className="unknown-lightbox"
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedSighting(null)}
        >
          <div className="unknown-lightbox-content" onClick={(event) => event.stopPropagation()}>
            <button
              className="unknown-lightbox-close"
              onClick={() => setSelectedSighting(null)}
              aria-label="Close"
            >
              ×
            </button>
            <img src={selectedSighting.snapshot_url} alt="Camera log full view" />
            <div>
              <strong>{selectedSighting.camera_name || "Camera"}</strong>
              <span>{new Date(selectedSighting.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

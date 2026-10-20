import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Icon from "../components/Icon";

const ANGLE_SLOTS = [
  { key: "front", label: "Front" },
  { key: "left", label: "Left" },
  { key: "right", label: "Right" },
  { key: "up", label: "Up" },
  { key: "down", label: "Down" },
] as const;

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

type AngleKey = (typeof ANGLE_SLOTS)[number]["key"];

export default function PersonEnrollPage() {
  const navigate = useNavigate();
  const [orgId, setOrgId] = useState("");
  const [fullName, setFullName] = useState("");
  const [personType, setPersonType] = useState("student");
  const [department, setDepartment] = useState("");
  const [photos, setPhotos] = useState<Partial<Record<AngleKey, File>>>({});
  const [previews, setPreviews] = useState<Partial<Record<AngleKey, string>>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [scanInfo, setScanInfo] = useState("");
  const fileRefs = useRef<Partial<Record<AngleKey, HTMLInputElement | null>>>({});

  const filledAngles = ANGLE_SLOTS.filter((slot) => Boolean(photos[slot.key])).length;
  const allAnglesReady = filledAngles === ANGLE_SLOTS.length;

  useEffect(() => {
    api
      .getOrganizations()
      .then((orgs) => setOrgId(orgs.results?.[0]?.id || ""))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load organization"));
  }, []);

  useEffect(() => {
    return () => {
      Object.values(previews).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [previews]);

  function setAnglePhoto(angle: AngleKey, file: File | null) {
    setPhotos((current) => {
      const next = { ...current };
      if (file) next[angle] = file;
      else delete next[angle];
      return next;
    });
    setPreviews((current) => {
      const next = { ...current };
      if (current[angle]) URL.revokeObjectURL(current[angle]!);
      if (file) next[angle] = URL.createObjectURL(file);
      else delete next[angle];
      return next;
    });
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError("");
    setScanInfo("");
    if (!allAnglesReady) {
      const missing = ANGLE_SLOTS.filter((slot) => !photos[slot.key]).map((slot) => slot.label);
      setError(`Add all 5 angles first. Missing: ${missing.join(", ")}.`);
      return;
    }
    if (!orgId) {
      setError("No organization found.");
      return;
    }
    setSaving(true);
    try {
      await api.createPerson({
        organization: orgId,
        full_name: fullName,
        person_type: personType,
        department,
        external_id: "",
      });
      const created = await api.getPersons();
      const person = created.results.find((p) => p.full_name === fullName && !p.embedding_count);
      if (!person) {
        throw new Error("Profile created but could not start enrollment.");
      }
      await api.createConsent({
        organization: orgId,
        person: person.id,
        consent_type: "enrollment",
        granted_at: new Date().toISOString(),
      });
      const enrolled = await api.enrollPersonWithImages(person.id, photos);
      if (enrolled.issue) {
        setError(`Issue: ${enrolled.issue}`);
        setSaving(false);
        return;
      }
      setScanInfo(
        `Saved ${enrolled.angles_saved || 5}/5 angles · ${enrolled.embedding_count || 5} profiles`
      );
      navigate(`/persons?selected=${person.id}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="person-enroll-page">
      <header className="page-header person-enroll-header">
        <div>
          <Link to="/persons" className="person-enroll-back">
            ← Back to profiles
          </Link>
          <h1>Add new person</h1>
          <p className="muted">Upload all 5 face angles, then save to enroll.</p>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}
      {scanInfo && <p className="scan-ok-pill">{scanInfo}</p>}

      <form className="enroll-card person-enroll-form" onSubmit={handleCreate}>
        <div className="enroll-angles">
          <strong>Full human view — all 5 angles required</strong>
          <p className="muted small">
            Front, Left, Right, Up and Down clear face photos. Then AI matures the identity.
          </p>
          <div className="enroll-progress">
            <span className={allAnglesReady ? "ready" : ""}>
              {filledAngles}/5 angles · {allAnglesReady ? "Ready to save" : "Incomplete"}
            </span>
          </div>
          <div className="enroll-angle-grid">
            {ANGLE_SLOTS.map((slot) => (
              <button
                key={slot.key}
                type="button"
                className={`enroll-angle-slot ${previews[slot.key] ? "has-photo" : "required-empty"}`}
                onClick={() => fileRefs.current[slot.key]?.click()}
              >
                {previews[slot.key] ? (
                  <img src={previews[slot.key]} alt={slot.label} />
                ) : (
                  <Icon name="people" />
                )}
                <span>
                  {slot.label}
                  {previews[slot.key] ? " ✓" : " *"}
                </span>
                <input
                  ref={(el) => {
                    fileRefs.current[slot.key] = el;
                  }}
                  type="file"
                  accept="image/*"
                  capture="user"
                  hidden
                  onChange={(e) => setAnglePhoto(slot.key, e.target.files?.[0] ?? null)}
                />
              </button>
            ))}
          </div>
        </div>

        <label>
          Full name
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label>
          Type
          <select value={personType} onChange={(e) => setPersonType(e.target.value)}>
            {PERSON_TYPES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Department (optional)
          <input value={department} onChange={(e) => setDepartment(e.target.value)} />
        </label>

        <div className="person-enroll-actions">
          <Link to="/persons" className="btn secondary">
            Cancel
          </Link>
          <button type="submit" className="btn" disabled={saving || !orgId || !allAnglesReady}>
            {saving
              ? "Saving + AI enroll…"
              : allAnglesReady
                ? "Save profile"
                : `Add all angles (${filledAngles}/5)`}
          </button>
        </div>
      </form>
    </div>
  );
}

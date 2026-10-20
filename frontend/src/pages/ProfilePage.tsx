import { useEffect, useState } from "react";
import { api, Organization } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Icon from "../components/Icon";

type Membership = { organization: Organization; role: string };

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [error, setError] = useState("");
  const initials = (user || "AD").slice(0, 2).toUpperCase();
  const primaryRole = memberships[0]?.role || "operator";
  const primaryOrg = memberships[0]?.organization?.name || "—";

  useEffect(() => {
    let cancelled = false;
    api
      .getMyMemberships()
      .then((data) => {
        if (!cancelled) setMemberships(Array.isArray(data) ? data : []);
      })
      .catch((cause) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Failed to load profile");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <header className="page-header">
        <h1>Profile</h1>
        <p className="muted">Account details and organization access</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="profile-card">
        <div className="profile-hero">
          <span className="profile-avatar">{initials}</span>
          <div>
            <h2>{user || "Administrator"}</h2>
            <p className="muted">Signed in to SentinelVision</p>
          </div>
        </div>

        <div className="profile-fields">
          <div className="profile-field">
            <span className="muted">Username</span>
            <strong>{user || "—"}</strong>
          </div>
          <div className="profile-field">
            <span className="muted">Role</span>
            <strong className="badge online" style={{ textTransform: "capitalize" }}>{primaryRole}</strong>
          </div>
          <div className="profile-field">
            <span className="muted">Organization</span>
            <strong>{primaryOrg}</strong>
          </div>
        </div>

        {memberships.length > 1 && (
          <>
            <div className="section-title" style={{ marginTop: "1.25rem" }}>
              <span className="bar" /> Memberships
            </div>
            <div className="profile-memberships">
              {memberships.map((item) => (
                <div className="profile-membership" key={`${item.organization.id}-${item.role}`}>
                  <strong>{item.organization.name}</strong>
                  <span className="badge" style={{ textTransform: "capitalize" }}>{item.role}</span>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="row-actions" style={{ marginTop: "1.25rem" }}>
          <button type="button" onClick={logout}>
            <Icon name="logout" /> Sign out
          </button>
        </div>
      </section>
    </div>
  );
}

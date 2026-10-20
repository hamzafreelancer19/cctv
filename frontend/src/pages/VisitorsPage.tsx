import { FormEvent, useEffect, useState } from "react";
import { api, Visitor } from "../api/client";

export default function VisitorsPage() {
  const [visitors, setVisitors] = useState<Visitor[]>([]);
  const [orgId, setOrgId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [fullName, setFullName] = useState("");
  const [hostName, setHostName] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const orgs = await api.getOrganizations();
      setOrgId(orgs.results?.[0]?.id || "");
      const sites = await api.getSites();
      setSiteId(sites.results?.[0]?.id || "");
      const data = await api.getVisitors();
      setVisitors(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    const now = new Date();
    const until = new Date(now.getTime() + 24 * 3600 * 1000);
    try {
      await api.createVisitor({
        organization: orgId,
        site: siteId,
        full_name: fullName,
        host_name: hostName || "Host",
        purpose: "Visit",
        valid_from: now.toISOString(),
        valid_until: until.toISOString(),
      });
      setFullName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function act(id: string, action: string) {
    try {
      await api.visitorAction(id, action);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Visitor Management</h1>
        <p className="muted">Request → approve → QR → check-in / check-out</p>
      </header>
      <form className="login-card" style={{ marginBottom: "1.5rem", maxWidth: 480 }} onSubmit={handleCreate}>
        <label>
          Visitor name
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label>
          Host name
          <input value={hostName} onChange={(e) => setHostName(e.target.value)} />
        </label>
        <button type="submit">Create request</button>
      </form>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Host</th>
              <th>Status</th>
              <th>QR</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {visitors.map((v) => (
              <tr key={v.id}>
                <td>{v.full_name}</td>
                <td>{v.host_name}</td>
                <td>
                  <span className="badge">{v.status}</span>
                </td>
                <td>
                  <code>{v.qr_code.slice(0, 8)}…</code>
                </td>
                <td className="actions">
                  {v.status === "requested" && (
                    <>
                      <button onClick={() => act(v.id, "approve")}>Approve</button>
                      <button className="secondary" onClick={() => act(v.id, "deny")}>
                        Deny
                      </button>
                    </>
                  )}
                  {v.status === "approved" && <button onClick={() => act(v.id, "checkin")}>Check in</button>}
                  {v.status === "checked_in" && <button onClick={() => act(v.id, "checkout")}>Check out</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

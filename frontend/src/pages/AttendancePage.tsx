import { useEffect, useState } from "react";
import { api, AttendanceRecord, AttendanceReport } from "../api/client";

export default function AttendancePage() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [report, setReport] = useState<AttendanceReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const orgs = await api.getOrganizations();
        const orgId = orgs.results?.[0]?.id;
        const [list, summary] = await Promise.all([
          api.getAttendance(),
          orgId ? api.getAttendanceReport(orgId) : Promise.resolve(null),
        ]);
        if (!cancelled) {
          setRecords(list.results);
          setReport(summary);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed");
      }
    };
    load();
    const t = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <header className="page-header">
        <h1>Attendance</h1>
        <p className="muted">Auto clock-in/out from face recognition</p>
      </header>
      {report && (
        <section className="metric-grid" style={{ marginBottom: "1.5rem" }}>
          <article className="metric-card">
            <span className="metric-value">{report.clock_ins}</span>
            <span className="metric-label">Clock Ins</span>
          </article>
          <article className="metric-card">
            <span className="metric-value">{report.clock_outs}</span>
            <span className="metric-label">Clock Outs</span>
          </article>
          <article className="metric-card warning">
            <span className="metric-value">{report.late_count}</span>
            <span className="metric-label">Late</span>
          </article>
          <article className="metric-card">
            <span className="metric-value">{report.overtime_count}</span>
            <span className="metric-label">Overtime</span>
          </article>
        </section>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Person</th>
              <th>Direction</th>
              <th>Late</th>
              <th>Overtime</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.recorded_at).toLocaleString()}</td>
                <td>{r.person_name}</td>
                <td>{r.direction}</td>
                <td>{r.is_late ? "yes" : "—"}</td>
                <td>{r.is_overtime ? "yes" : "—"}</td>
                <td>{(r.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

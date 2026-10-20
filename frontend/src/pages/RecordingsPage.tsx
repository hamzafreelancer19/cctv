import { useEffect, useState } from "react";
import { api, RecordingJob } from "../api/client";
import Icon from "../components/Icon";

const vendorLabels: Record<string, string> = {
  rtsp: "Home / RTSP",
  onvif: "ONVIF",
  hikvision: "Hikvision",
  dahua: "Dahua",
  milestone: "Milestone",
  axis: "Axis",
  stub: "Stub",
};

export default function RecordingsPage() {
  const [jobs, setJobs] = useState<RecordingJob[]>([]);
  const [recordingCount, setRecordingCount] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .getRecordings()
        .then((data) => !cancelled && setJobs(data.results))
        .catch((e) => !cancelled && setError(e.message));
      api
        .getRecorderStatus()
        .then((status) => !cancelled && setRecordingCount(status.count))
        .catch(() => undefined);
    };
    load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (error) return <div className="error-banner">{error}</div>;

  const continuous = jobs.filter((j) => j.details?.mode === "continuous").length;

  return (
    <div>
      <header className="page-header">
        <div>
          <h1>Recordings</h1>
          <p className="muted">
            Continuous home-camera clips (~60s each) plus event-triggered evidence — auto-refresh 5s
          </p>
        </div>
        <div className="camera-summary">
          <span>{recordingCount} cameras recording now</span>
          <span>{continuous} continuous clips</span>
        </div>
      </header>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Camera</th>
              <th>Type</th>
              <th>Source</th>
              <th>Status</th>
              <th>Clip</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => {
              const isContinuous = j.details?.mode === "continuous";
              const dur =
                j.started_at && j.ended_at
                  ? `${Math.max(
                      0,
                      Math.round((new Date(j.ended_at).getTime() - new Date(j.started_at).getTime()) / 1000)
                    )}s`
                  : j.status === "recording"
                    ? "live…"
                    : "—";
              return (
                <tr key={j.id}>
                  <td>{new Date(j.created_at).toLocaleString()}</td>
                  <td>{j.camera_name}</td>
                  <td>
                    <span className={`badge ${isContinuous ? "online" : "info"}`}>
                      {isContinuous ? "Continuous" : "Event"}
                    </span>
                  </td>
                  <td>{vendorLabels[j.vendor] || j.vendor}</td>
                  <td>
                    <span className={`badge ${j.status}`}>{j.status}</span>
                  </td>
                  <td>
                    {j.evidence_url ? (
                      <a href={j.evidence_url} target="_blank" rel="noreferrer" className="badge info">
                        Open clip
                      </a>
                    ) : (
                      <span className="muted">{j.clip_key || "—"}</span>
                    )}
                  </td>
                  <td>{dur}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {jobs.length === 0 && (
          <div className="empty-state">
            <span className="empty-ic"><Icon name="recording" /></span>
            No recordings yet. Connect a home camera with <strong>Auto record</strong> enabled —
            clips will appear here every ~60 seconds.
          </div>
        )}
      </div>
    </div>
  );
}

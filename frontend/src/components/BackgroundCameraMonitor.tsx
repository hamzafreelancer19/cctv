import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../api/client";
import Icon from "./Icon";

type MonitorStatus = {
  active: boolean;
  lastOk: number;
  lastChecked: number;
  lastAt: string;
};

/**
 * Keeps camera detect + capture running on EVERY page (Events, Unknown, Alerts…).
 * On /cameras the live cards already poll — this runs a lighter background tick
 * everywhere else so monitoring never stops when you leave the camera page.
 */
export default function BackgroundCameraMonitor() {
  const location = useLocation();
  const onCamerasPage = location.pathname.startsWith("/cameras");
  const [status, setStatus] = useState<MonitorStatus>({
    active: false,
    lastOk: 0,
    lastChecked: 0,
    lastAt: "",
  });

  useEffect(() => {
    let cancelled = false;
    let running = false;
    let timer = 0;

    const tick = async () => {
      if (cancelled || running) return;
      running = true;
      try {
        const result = await api.monitorCamerasTick(!onCamerasPage);
        if (!cancelled) {
          setStatus({
            active: true,
            lastOk: result.ok,
            lastChecked: result.checked,
            lastAt: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            }),
          });
        }
      } catch {
        if (!cancelled) {
          setStatus((prev) => ({ ...prev, active: false }));
        }
      } finally {
        running = false;
        if (!cancelled) {
          // Faster when away from cameras so capture still feels real-time.
          // On /cameras live cards already run YOLO — tick lightly without vision.
          const delay = onCamerasPage ? 12000 : 4000;
          timer = window.setTimeout(tick, delay);
        }
      }
    };

    timer = window.setTimeout(tick, onCamerasPage ? 4000 : 800);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [onCamerasPage]);

  if (!status.active && !status.lastAt) return null;

  const checked = status.lastChecked || 0;
  const online = status.lastOk;
  const title = status.active
    ? `Cameras online ${online}/${checked || "…"}${status.lastAt ? ` · last check ${status.lastAt}` : ""}`
    : "Camera monitor reconnecting…";

  return (
    <span className={`monitor-pill ${status.active ? "on" : "off"}`} title={title}>
      <Icon name="camera" />
      {status.active ? (
        <>
          <span className="monitor-label">Cameras</span>
          <strong>
            {online}/{checked || "…"}
          </strong>
        </>
      ) : (
        <span className="monitor-label">Reconnecting</span>
      )}
    </span>
  );
}

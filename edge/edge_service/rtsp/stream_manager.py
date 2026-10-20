"""Sprint 1 — RTSP / video stream manager with reconnect and FPS monitoring."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Callable

from edge_service.types import FramePacket, StreamHealth

logger = logging.getLogger(__name__)


class CameraStream:
    """Single camera capture thread with reconnect and frame sampling queue."""

    def __init__(
        self,
        camera_id: str,
        source: str,
        name: str = "",
        queue_size: int = 8,
        reconnect_delay: float = 3.0,
        reconnect_max_delay: float = 60.0,
        target_fps: float = 5.0,
    ):
        self.camera_id = camera_id
        self.source = source
        self.name = name or camera_id
        self.queue_size = queue_size
        self.reconnect_delay = reconnect_delay
        self.reconnect_max_delay = reconnect_max_delay
        self.target_fps = max(0.5, target_fps)

        self._queue: deque[FramePacket] = deque(maxlen=queue_size)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._cap = None
        self.health = StreamHealth(camera_id=camera_id, source=source, connected=False)
        self._lock = threading.Lock()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"stream-{self.name}", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._release()

    def get_latest(self) -> FramePacket | None:
        with self._lock:
            return self._queue[-1] if self._queue else None

    def pop_latest(self) -> FramePacket | None:
        with self._lock:
            return self._queue.pop() if self._queue else None

    def _open(self) -> bool:
        try:
            import cv2

            source: str | int = self.source
            if self.source.isdigit():
                source = int(self.source)
            # Prefer FFmpeg backend for RTSP when available
            if isinstance(source, str) and source.lower().startswith("rtsp"):
                self._cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                try:
                    self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
            else:
                self._cap = cv2.VideoCapture(source)
            ok = bool(self._cap is not None and self._cap.isOpened())
            self.health.connected = ok
            if not ok:
                self.health.last_error = "Failed to open source"
            else:
                self.health.last_error = ""
                logger.info("Opened stream %s (%s)", self.name, self.source)
            return ok
        except Exception as exc:
            self.health.connected = False
            self.health.last_error = str(exc)
            logger.error("Open stream failed %s: %s", self.name, exc)
            return False

    def _release(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self.health.connected = False

    def _run(self):
        delay = self.reconnect_delay
        min_interval = 1.0 / self.target_fps
        frame_index = 0
        fps_window_start = time.time()
        fps_count = 0

        while not self._stop.is_set():
            if self._cap is None or not self.health.connected:
                if not self._open():
                    self.health.reconnect_count += 1
                    time.sleep(delay)
                    delay = min(delay * 1.5, self.reconnect_max_delay)
                    continue
                delay = self.reconnect_delay

            loop_start = time.time()
            try:
                ret, frame = self._cap.read()
            except Exception as exc:
                self.health.last_error = str(exc)
                self._release()
                continue

            if not ret or frame is None:
                self.health.last_error = "Frame read failed"
                self._release()
                self.health.reconnect_count += 1
                time.sleep(delay)
                delay = min(delay * 1.5, self.reconnect_max_delay)
                continue

            now = time.time()
            h, w = frame.shape[:2]
            packet = FramePacket(
                camera_id=self.camera_id,
                camera_name=self.name,
                source=self.source,
                frame=frame,
                timestamp=now,
                frame_index=frame_index,
                width=w,
                height=h,
            )
            with self._lock:
                self._queue.append(packet)
            frame_index += 1
            self.health.frames_read += 1
            self.health.last_frame_ts = now
            self.health.connected = True
            self.health.last_error = ""

            fps_count += 1
            if now - fps_window_start >= 1.0:
                self.health.fps = fps_count / (now - fps_window_start)
                fps_window_start = now
                fps_count = 0

            elapsed = time.time() - loop_start
            sleep_for = min_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)


class StreamManager:
    """Manages multiple camera streams."""

    def __init__(self):
        self._streams: dict[str, CameraStream] = {}

    def add_camera(
        self,
        camera_id: str,
        source: str,
        name: str = "",
        queue_size: int = 8,
        reconnect_delay: float = 3.0,
        reconnect_max_delay: float = 60.0,
        target_fps: float = 5.0,
    ) -> CameraStream:
        if camera_id in self._streams:
            self._streams[camera_id].stop()
        stream = CameraStream(
            camera_id=camera_id,
            source=source,
            name=name,
            queue_size=queue_size,
            reconnect_delay=reconnect_delay,
            reconnect_max_delay=reconnect_max_delay,
            target_fps=target_fps,
        )
        self._streams[camera_id] = stream
        stream.start()
        return stream

    def remove_camera(self, camera_id: str):
        stream = self._streams.pop(camera_id, None)
        if stream:
            stream.stop()

    def get(self, camera_id: str) -> CameraStream | None:
        return self._streams.get(camera_id)

    def all_health(self) -> list[StreamHealth]:
        return [s.health for s in self._streams.values()]

    def iter_latest(self) -> list[FramePacket]:
        packets = []
        for stream in self._streams.values():
            pkt = stream.pop_latest()
            if pkt is not None:
                packets.append(pkt)
        return packets

    def stop_all(self):
        for stream in list(self._streams.values()):
            stream.stop()
        self._streams.clear()

    @property
    def camera_ids(self) -> list[str]:
        return list(self._streams.keys())

"""Small rolling frame buffer for verified safety evidence clips."""

from collections import deque
from pathlib import Path
from typing import Any
import uuid


class EvidenceBuffer:
    def __init__(self, seconds: float = 5.0, fps: float = 5.0):
        self.fps = max(1.0, fps)
        self.frames: deque[Any] = deque(maxlen=max(2, int(seconds * self.fps)))

    def add(self, frame: Any):
        if frame is not None:
            self.frames.append(frame.copy())

    def save(self, directory: str, camera_id: str, event_type: str) -> str:
        if not self.frames:
            return ""
        try:
            import cv2

            path = Path(directory) / "evidence"
            path.mkdir(parents=True, exist_ok=True)
            output = path / f"{camera_id}_{event_type}_{uuid.uuid4().hex[:8]}.mp4"
            height, width = self.frames[0].shape[:2]
            writer = cv2.VideoWriter(
                str(output),
                cv2.VideoWriter_fourcc(*"mp4v"),
                self.fps,
                (width, height),
            )
            if not writer.isOpened():
                return ""
            for frame in self.frames:
                writer.write(frame)
            writer.release()
            return str(output)
        except Exception:
            return ""

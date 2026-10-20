"""AI module adapters — placeholders for OpenCV, YOLO, InsightFace integration."""

from __future__ import annotations

import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DetectionResult:
    event_type: str
    severity: str
    confidence: float
    model_name: str
    model_version: str
    payload: dict[str, Any] = field(default_factory=dict)


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, frame: Any | None = None) -> list[DetectionResult]:
        pass


class SimulatedYOLODetector(BaseDetector):
    """Simulates YOLO person detection until production models are deployed."""

    MODEL_NAME = "yolo-sim"
    MODEL_VERSION = "0.1.0"

    def detect(self, frame: Any | None = None) -> list[DetectionResult]:
        if random.random() > 0.6:
            return []
        track_id = random.randint(1, 100)
        confidence = round(random.uniform(0.55, 0.98), 2)
        return [
            DetectionResult(
                event_type="person_detected",
                severity="warning" if confidence < 0.8 else "info",
                confidence=confidence,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                payload={
                    "track_id": track_id,
                    "bbox": [random.randint(50, 200), random.randint(50, 200), 120, 280],
                    "simulated": True,
                },
            )
        ]


class OpenCVStreamAdapter:
    """RTSP stream adapter using OpenCV (placeholder for production pipeline)."""

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self._cap = None

    def connect(self) -> bool:
        try:
            import cv2

            self._cap = cv2.VideoCapture(self.rtsp_url)
            return self._cap.isOpened()
        except Exception:
            return False

    def read_frame(self):
        if self._cap is None:
            return None
        import cv2

        ret, frame = self._cap.read()
        return frame if ret else None

    def release(self):
        if self._cap:
            self._cap.release()


def build_event_payload(camera_id: str, detection: DetectionResult) -> dict:
    return {
        "camera_id": camera_id,
        "event_type": detection.event_type,
        "severity": detection.severity,
        "confidence": detection.confidence,
        "model_name": detection.model_name,
        "model_version": detection.model_version,
        "payload": detection.payload,
        "edge_event_id": str(uuid.uuid4()),
    }

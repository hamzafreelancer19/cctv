"""Sprint 2 — YOLO detection service with GPU/CPU fallback and simulated backend."""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from typing import Any

from edge_service.types import BoundingBox, Detection

logger = logging.getLogger(__name__)


class BaseDetector(ABC):
    model_name: str = "detector"
    model_version: str = "0.0.0"

    @abstractmethod
    def detect(self, frame: Any) -> list[Detection]:
        raise NotImplementedError


class SimulatedDetector(BaseDetector):
    """Deterministic-enough simulator for CI and environments without YOLO weights."""

    model_name = "yolo-sim"
    model_version = "0.2.0"

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold

    def detect(self, frame: Any) -> list[Detection]:
        if frame is None:
            return []
        detections: list[Detection] = []
        h, w = frame.shape[:2]
        if random.random() <= 0.55:
            conf = round(random.uniform(max(self.confidence_threshold, 0.55), 0.98), 3)
            bw, bh = int(w * 0.12), int(h * 0.35)
            x1 = random.randint(0, max(1, w - bw))
            y1 = random.randint(0, max(1, h - bh))
            detections.append(
                Detection(
                    bbox=BoundingBox(x1, y1, x1 + bw, y1 + bh),
                    confidence=conf,
                    class_id=0,
                    class_name="person",
                )
            )
        # Occasional stationary-looking object for M4 left/removed sim
        if random.random() < 0.25:
            conf = round(random.uniform(0.6, 0.95), 3)
            ow, oh = int(w * 0.08), int(h * 0.08)
            # Prefer a stable corner so object tracker can mark stationary
            x1 = int(w * 0.7)
            y1 = int(h * 0.7)
            detections.append(
                Detection(
                    bbox=BoundingBox(x1, y1, x1 + ow, y1 + oh),
                    confidence=conf,
                    class_id=24,
                    class_name=random.choice(["bag", "laptop", "package"]),
                )
            )
        return detections


class YOLODetector(BaseDetector):
    """Ultralytics YOLO wrapper. Falls back is handled by factory."""

    model_name = "yolov8"
    model_version = "ultralytics"

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str = "auto",
        person_class_id: int = 0,
    ):
        from ultralytics import YOLO

        self.confidence_threshold = confidence_threshold
        self.person_class_id = person_class_id
        self.device = self._resolve_device(device)
        self.model = YOLO(model_path)
        self.model_name = model_path
        logger.info("YOLO loaded model=%s device=%s", model_path, self.device)

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch

            return "0" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def detect(self, frame: Any) -> list[Detection]:
        if frame is None:
            return []
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            device=self.device,
            verbose=False,
        )
        detections: list[Detection] = []
        if not results:
            return detections
        result = results[0]
        if result.boxes is None:
            return detections
        for box in result.boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0].item()) if box.conf is not None else 0.0
            cls_id = int(box.cls[0].item()) if box.cls is not None else 0
            names = getattr(result, "names", {}) or {}
            class_name = str(names.get(cls_id, cls_id))
            detections.append(
                Detection(
                    bbox=BoundingBox(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                    confidence=conf,
                    class_id=cls_id,
                    class_name=class_name,
                )
            )
        return detections


def create_detector(
    backend: str = "auto",
    model_path: str = "yolov8n.pt",
    confidence_threshold: float = 0.5,
    device: str = "auto",
    person_class_id: int = 0,
) -> BaseDetector:
    backend = (backend or "auto").lower()
    if backend == "simulated":
        return SimulatedDetector(confidence_threshold)

    if backend in ("auto", "yolo"):
        try:
            return YOLODetector(
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device,
                person_class_id=person_class_id,
            )
        except Exception as exc:
            if backend == "yolo":
                raise
            logger.warning("YOLO unavailable (%s); using SimulatedDetector", exc)
            return SimulatedDetector(confidence_threshold)

    raise ValueError(f"Unknown detection backend: {backend}")

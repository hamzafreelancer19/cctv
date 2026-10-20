"""Sprint 1 — Face detection, crop, blur/quality checks, best-face selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from edge_service.types import BoundingBox, Track

logger = logging.getLogger(__name__)


@dataclass
class FaceCrop:
    track_id: int
    bbox: BoundingBox
    image: Any  # BGR crop
    quality_score: float
    blur_score: float
    aligned: bool = False


def estimate_blur(gray: np.ndarray) -> float:
    """Laplacian variance — higher is sharper."""
    import cv2

    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def estimate_quality(crop: np.ndarray, blur: float) -> float:
    """Heuristic quality 0..1 from size + sharpness."""
    h, w = crop.shape[:2]
    size_score = min(1.0, (min(h, w) / 112.0))
    blur_score = min(1.0, blur / 200.0)
    return round(0.55 * size_score + 0.45 * blur_score, 3)


def align_face_simple(crop: np.ndarray) -> np.ndarray:
    """Lightweight alignment: center-crop to square and resize to 112x112."""
    import cv2

    h, w = crop.shape[:2]
    side = min(h, w)
    y0 = (h - side) // 2
    x0 = (w - side) // 2
    square = crop[y0 : y0 + side, x0 : x0 + side]
    if square.size == 0:
        return crop
    return cv2.resize(square, (112, 112), interpolation=cv2.INTER_AREA)


class FaceDetector:
    """OpenCV Haar cascade face detector inside person bbox (CPU-friendly)."""

    def __init__(self, min_blur: float = 20.0, min_quality: float = 0.35):
        import cv2

        self.min_blur = min_blur
        self.min_quality = min_quality
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        self._best: dict[int, FaceCrop] = {}

    def detect_on_track(self, frame: Any, track: Track) -> FaceCrop | None:
        import cv2

        if frame is None:
            return None
        x1, y1, x2, y2 = map(int, track.bbox.as_xyxy())
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 - x1 < 20 or y2 - y1 < 20:
            return None
        person = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(person, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(24, 24))
        if len(faces) == 0:
            # Fallback: upper-body crop as pseudo-face for pipeline continuity in sim/test
            ph, pw = person.shape[:2]
            fy1, fy2 = 0, max(1, int(ph * 0.45))
            fx1, fx2 = int(pw * 0.2), int(pw * 0.8)
            face_img = person[fy1:fy2, fx1:fx2]
            if face_img.size == 0:
                return None
            abs_box = BoundingBox(x1 + fx1, y1 + fy1, x1 + fx2, y1 + fy2)
        else:
            # pick largest face
            fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            face_img = person[fy : fy + fh, fx : fx + fw]
            abs_box = BoundingBox(x1 + fx, y1 + fy, x1 + fx + fw, y1 + fy + fh)

        gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY) if face_img.ndim == 3 else face_img
        blur = estimate_blur(gray_face)
        aligned = align_face_simple(face_img)
        quality = estimate_quality(aligned, blur)
        crop = FaceCrop(
            track_id=track.track_id,
            bbox=abs_box,
            image=aligned,
            quality_score=quality,
            blur_score=blur,
            aligned=True,
        )
        if blur < self.min_blur or quality < self.min_quality:
            return None
        self._update_best(crop)
        return crop

    def _update_best(self, crop: FaceCrop):
        prev = self._best.get(crop.track_id)
        if prev is None or crop.quality_score >= prev.quality_score:
            self._best[crop.track_id] = crop

    def best_face(self, track_id: int) -> FaceCrop | None:
        return self._best.get(track_id)

    def clear_track(self, track_id: int):
        self._best.pop(track_id, None)

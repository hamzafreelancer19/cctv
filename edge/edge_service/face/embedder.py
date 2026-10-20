"""Sprint 3 — Face embedding (InsightFace optional) + gallery match client helpers."""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


class FaceEmbedder:
    model_name = "insightface-sim"
    model_version = "0.1.0"

    def __init__(self, backend: str = "auto"):
        self.backend = backend
        self._app = None
        if backend in ("auto", "insightface"):
            try:
                from insightface.app import FaceAnalysis

                self._app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
                self._app.prepare(ctx_id=-1, det_size=(640, 640))
                self.model_name = "insightface"
                self.model_version = "buffalo_l"
                logger.info("InsightFace loaded")
            except Exception as exc:
                if backend == "insightface":
                    raise
                logger.warning("InsightFace unavailable (%s); using simulated embeddings", exc)

    def embed(self, face_bgr: Any) -> list[float]:
        if self._app is not None:
            faces = self._app.get(face_bgr)
            if faces:
                return l2_normalize(faces[0].embedding.astype(float).tolist())
        # Deterministic simulated embedding from image bytes
        raw = np.ascontiguousarray(face_bgr).tobytes()
        digest = hashlib.sha256(raw).digest()
        values: list[float] = []
        seed = digest
        while len(values) < 128:
            seed = hashlib.sha256(seed).digest()
            for b in seed:
                values.append((b / 127.5) - 1.0)
                if len(values) >= 128:
                    break
        return l2_normalize(values)


class LocalGallery:
    def __init__(self):
        self.entries: list[dict] = []

    def load(self, results: list[dict]):
        self.entries = results or []

    def match(self, embedding: list[float], threshold: float = 0.45) -> tuple[dict | None, float]:
        best = None
        best_score = -1.0
        q = l2_normalize(embedding)
        for entry in self.entries:
            vec = entry.get("vector") or []
            score = cosine_similarity(q, l2_normalize(vec))
            if score > best_score:
                best_score = score
                best = entry
        if best is None or best_score < threshold:
            return None, max(best_score, 0.0)
        return best, best_score

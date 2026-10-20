"""Embedding utilities — OpenCV SFace identity particles (fallback: LBP)."""

from __future__ import annotations

import hashlib
import math
from typing import Iterable

import numpy as np

APPEARANCE_MODEL = "opencv-sface"
# Bump forces gallery re-embed after SFace backend change (OpenCV FaceRecognizerSF).
APPEARANCE_VERSION = "3.2.0"
APPEARANCE_DIM = 128

# SFace cosine — official ~0.363; CCTV live a bit lower, but stay strict
# so strangers are not mislabeled as saved members.
DEFAULT_MATCH_THRESHOLD = 0.32
DEFAULT_MATCH_MARGIN = 0.05


def l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def simulate_embedding_from_bytes(data: bytes, dim: int = 128) -> list[float]:
    digest = hashlib.sha256(data).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dim:
        seed = hashlib.sha256(seed).digest()
        for byte in seed:
            values.append((byte / 127.5) - 1.0)
            if len(values) >= dim:
                break
    return l2_normalize(values)


def appearance_embedding_from_bytes(data: bytes, dim: int = APPEARANCE_DIM) -> list[float]:
    """
    Extract face identity particles from an image.

    Prefers OpenCV SFace (real face AI). Falls back to local LBP if models
    are missing or no face can be embedded.
    """
    try:
        from .face_ai import embed_image_bytes, models_available

        if models_available():
            vector = embed_image_bytes(data)
            if vector and len(vector) == APPEARANCE_DIM:
                return l2_normalize(vector)
    except Exception:
        pass

    return _lbp_embedding_from_bytes(data, dim=dim)


def _lbp_embedding_from_bytes(data: bytes, dim: int = 128) -> list[float]:
    """Compact fallback descriptor when SFace is unavailable."""
    try:
        import cv2
    except Exception:
        return simulate_embedding_from_bytes(data, dim=dim)

    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        return simulate_embedding_from_bytes(data, dim=dim)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    gray = cv2.equalizeHist(gray)
    flat = (gray.astype(np.float32) / 255.0 * 2.0) - 1.0
    vector = flat.flatten()
    if len(vector) < dim:
        vector = np.pad(vector, (0, dim - len(vector)))
    else:
        vector = vector[:dim]
    return l2_normalize(vector.tolist())


def best_match(
    query: list[float],
    gallery: Iterable[tuple[str, list[float]]],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    min_margin: float = DEFAULT_MATCH_MARGIN,
) -> tuple[str | None, float]:
    """
    Return (person_id, score) or (None, best_score).

    Multi-angle strong match:
    - Keep the best score per person across angle + mature vectors
    - Also keep the 2nd-best angle score; if both angles agree, accept
      slightly below the hard threshold (mature multi-view confirmation)
    - Still require a margin vs a different person
    """
    query_n = l2_normalize(query)
    # person_id -> list of scores (one per embedding/angle)
    scores_by_person: dict[str, list[float]] = {}

    for person_id, vector in gallery:
        if len(vector) != len(query_n):
            continue
        score = cosine_similarity(query_n, l2_normalize(vector))
        scores_by_person.setdefault(person_id, []).append(score)

    if not scores_by_person:
        return None, 0.0

    person_best: dict[str, float] = {}
    person_support: dict[str, float] = {}
    person_angles: dict[str, int] = {}
    for person_id, scores in scores_by_person.items():
        ranked_scores = sorted(scores, reverse=True)
        best = ranked_scores[0]
        second_angle = ranked_scores[1] if len(ranked_scores) > 1 else -1.0
        # Support score: average of top-2 angles (or best alone).
        support = (best + max(second_angle, 0.0)) / 2.0 if second_angle >= 0 else best
        person_best[person_id] = best
        person_support[person_id] = support
        person_angles[person_id] = len(ranked_scores)

    ranked = sorted(person_best.items(), key=lambda item: item[1], reverse=True)
    best_id, best_score = ranked[0]
    rival = ranked[1][1] if len(ranked) > 1 else -1.0
    support = person_support.get(best_id, best_score)
    angle_count = int(person_angles.get(best_id, 1))

    # Strong accept only. Soft path needs multi-angle support + clear margin
    # so one weak random hit never becomes a saved-member name.
    soft_threshold = max(0.28, threshold - 0.03)
    accepted = best_score >= threshold
    if not accepted and best_score >= soft_threshold and angle_count >= 2:
        if support >= soft_threshold and (best_score - rival) >= max(0.06, min_margin):
            accepted = True
    if not accepted:
        return None, best_score
    # Reject ambiguous ties between two enrolled people.
    if len(ranked) > 1 and (best_score - rival) < min_margin:
        return None, best_score
    return best_id, best_score

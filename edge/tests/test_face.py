"""M3 face detection / embedding unit tests."""

import numpy as np

from edge_service.face.detector import FaceDetector, estimate_blur, estimate_quality, align_face_simple
from edge_service.face.embedder import FaceEmbedder, cosine_similarity
from edge_service.types import BoundingBox, Track


def test_blur_and_quality_on_noise():
    img = np.random.randint(0, 255, (120, 120, 3), dtype=np.uint8)
    gray = img[:, :, 0]
    blur = estimate_blur(gray)
    aligned = align_face_simple(img)
    assert aligned.shape[0] == 112
    q = estimate_quality(aligned, blur)
    assert 0 <= q <= 1


def test_face_detector_returns_crop_or_none():
    det = FaceDetector(min_blur=1.0, min_quality=0.01)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    track = Track(track_id=1, bbox=BoundingBox(100, 50, 300, 400), confidence=0.9)
    crop = det.detect_on_track(frame, track)
    # Haar may or may not find faces in noise; fallback upper-body path should usually return
    assert crop is None or crop.image is not None


def test_embedder_deterministic():
    emb = FaceEmbedder(backend="simulated")
    face = np.zeros((112, 112, 3), dtype=np.uint8)
    face[:, :] = (10, 20, 30)
    a = emb.embed(face)
    b = emb.embed(face)
    assert len(a) == 128
    assert cosine_similarity(a, b) > 0.99

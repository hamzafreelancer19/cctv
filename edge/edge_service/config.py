"""Edge AI configuration for M2 RTSP / YOLO / tracking pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


@dataclass
class EdgeConfig:
    api_base_url: str
    edge_api_key: str
    camera_id: str
    heartbeat_interval: int
    simulation_interval: int
    version: str

    # M2 streaming
    mode: str = "auto"  # auto | rtsp | simulation
    detection_backend: str = "auto"  # auto | yolo | simulated
    yolo_model: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    target_infer_fps: float = 5.0
    frame_queue_size: int = 8
    reconnect_delay_sec: float = 3.0
    reconnect_max_delay_sec: float = 60.0
    device: str = "auto"  # auto | cpu | cuda | 0
    person_class_id: int = 0
    loitering_seconds: float = 120.0
    object_left_seconds: float = 20.0
    event_cooldown_sec: float = 15.0
    snapshot_dir: str = "snapshots"
    enable_snapshots: bool = False
    enable_face: bool = True
    face_backend: str = "auto"
    face_match_threshold: float = 0.45
    face_min_quality: float = 0.35
    face_min_blur: float = 20.0
    enable_safety: bool = True
    enable_safety_evidence: bool = False
    safety_evidence_seconds: float = 5.0
    camera_sources: list[dict] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "EdgeConfig":
        # Optional explicit source override: RTSP_URL=... or VIDEO_SOURCE=path|0
        sources: list[dict] = []
        rtsp = os.getenv("RTSP_URL", "").strip()
        video = os.getenv("VIDEO_SOURCE", "").strip()
        camera_id = os.getenv("CAMERA_ID", "").strip()
        if rtsp:
            sources.append({"camera_id": camera_id, "source": rtsp, "name": "env-rtsp"})
        elif video:
            sources.append({"camera_id": camera_id, "source": video, "name": "env-video"})

        return cls(
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/"),
            edge_api_key=os.getenv("EDGE_API_KEY", "edge-dev-api-key-change-in-production"),
            camera_id=camera_id,
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "30")),
            simulation_interval=int(os.getenv("SIMULATION_INTERVAL", "10")),
            version=os.getenv("EDGE_VERSION", "0.5.0-m5"),
            mode=os.getenv("EDGE_MODE", "auto").lower(),
            detection_backend=os.getenv("DETECTION_BACKEND", "auto").lower(),
            yolo_model=os.getenv("YOLO_MODEL", "yolov8n.pt"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
            target_infer_fps=float(os.getenv("TARGET_INFER_FPS", "5")),
            frame_queue_size=int(os.getenv("FRAME_QUEUE_SIZE", "8")),
            reconnect_delay_sec=float(os.getenv("RECONNECT_DELAY_SEC", "3")),
            reconnect_max_delay_sec=float(os.getenv("RECONNECT_MAX_DELAY_SEC", "60")),
            device=os.getenv("INFER_DEVICE", "auto"),
            person_class_id=int(os.getenv("PERSON_CLASS_ID", "0")),
            loitering_seconds=float(os.getenv("LOITERING_SECONDS", "120")),
            object_left_seconds=float(os.getenv("OBJECT_LEFT_SECONDS", "20")),
            event_cooldown_sec=float(os.getenv("EVENT_COOLDOWN_SEC", "15")),
            snapshot_dir=os.getenv("SNAPSHOT_DIR", "snapshots"),
            enable_snapshots=_bool("ENABLE_SNAPSHOTS", False),
            enable_face=_bool("ENABLE_FACE", True),
            face_backend=os.getenv("FACE_BACKEND", "auto").lower(),
            face_match_threshold=float(os.getenv("FACE_MATCH_THRESHOLD", "0.45")),
            face_min_quality=float(os.getenv("FACE_MIN_QUALITY", "0.35")),
            face_min_blur=float(os.getenv("FACE_MIN_BLUR", "20")),
            enable_safety=_bool("ENABLE_SAFETY", True),
            enable_safety_evidence=_bool("ENABLE_SAFETY_EVIDENCE", False),
            safety_evidence_seconds=float(os.getenv("SAFETY_EVIDENCE_SECONDS", "5")),
            camera_sources=sources,
        )

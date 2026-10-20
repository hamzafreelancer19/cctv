"""Shared detection / tracking data types for M2 pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BoundingBox:
    """Axis-aligned box in pixel coordinates: x1,y1,x2,y2."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    def as_xyxy(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    def as_xywh(self) -> list[int]:
        return [int(self.x1), int(self.y1), int(self.width), int(self.height)]

    def normalized_centroid(self, frame_w: int, frame_h: int) -> tuple[float, float]:
        if frame_w <= 0 or frame_h <= 0:
            return 0.0, 0.0
        return self.cx / frame_w, self.cy / frame_h

    def iou(self, other: "BoundingBox") -> float:
        ix1 = max(self.x1, other.x1)
        iy1 = max(self.y1, other.y1)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0


@dataclass
class Detection:
    bbox: BoundingBox
    confidence: float
    class_id: int = 0
    class_name: str = "person"
    track_id: int | None = None


@dataclass
class Track:
    track_id: int
    bbox: BoundingBox
    confidence: float
    class_name: str = "person"
    age: int = 1
    hits: int = 1
    time_since_update: int = 0
    first_seen_ts: float = 0.0
    last_seen_ts: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FramePacket:
    camera_id: str
    camera_name: str
    source: str
    frame: Any
    timestamp: float
    frame_index: int
    width: int
    height: int


@dataclass
class StreamHealth:
    camera_id: str
    source: str
    connected: bool
    reconnect_count: int = 0
    frames_read: int = 0
    fps: float = 0.0
    last_error: str = ""
    last_frame_ts: float = 0.0

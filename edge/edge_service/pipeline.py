"""M2 orchestration: streams → detect → track → zones → events."""

from __future__ import annotations

import logging
import time
from typing import Any

from edge_service.client import ControlPlaneClient
from edge_service.config import EdgeConfig
from edge_service.crowd import CrowdAnalyzer
from edge_service.events.builder import (
    EventCooldown,
    build_person_event,
    build_zone_event,
    save_snapshot,
)
from edge_service.face.detector import FaceDetector
from edge_service.face.embedder import FaceEmbedder
from edge_service.objects.tracker import ObjectStateTracker
from edge_service.rtsp.stream_manager import StreamManager
from edge_service.safety.analyzer import SafetyAnalyzer
from edge_service.safety.evidence import EvidenceBuffer
from edge_service.tracker.iou_tracker import IOUTracker
from edge_service.yolo.detector import BaseDetector, create_detector
from edge_service.zones.engine import ZoneConfig, ZoneEngine

logger = logging.getLogger(__name__)


class DetectionPipeline:
    def __init__(self, config: EdgeConfig, client: ControlPlaneClient):
        self.config = config
        self.client = client
        self.streams = StreamManager()
        self.detector: BaseDetector = create_detector(
            backend=config.detection_backend,
            model_path=config.yolo_model,
            confidence_threshold=config.confidence_threshold,
            device=config.device,
            person_class_id=config.person_class_id,
        )
        self.trackers: dict[str, IOUTracker] = {}
        self.zone_engines: dict[str, ZoneEngine] = {}
        self.face_detectors: dict[str, FaceDetector] = {}
        self.face_embedder = FaceEmbedder(backend=config.face_backend) if config.enable_face else None
        self.crowd = CrowdAnalyzer()
        self.object_trackers: dict[str, ObjectStateTracker] = {}
        self.safety_analyzers: dict[str, SafetyAnalyzer] = {}
        self.evidence_buffers: dict[str, EvidenceBuffer] = {}
        self.track_identities: dict[str, dict[int, dict[str, Any]]] = {}
        self.cooldown = EventCooldown(config.event_cooldown_sec)
        self._camera_meta: dict[str, dict[str, Any]] = {}
        self._last_gallery_sync = 0.0
        self.stats = {
            "frames_processed": 0,
            "detections": 0,
            "events_sent": 0,
            "events_failed": 0,
            "faces_matched": 0,
            "faces_unknown": 0,
            "crowd_events": 0,
            "object_events": 0,
            "safety_events": 0,
        }

    def bootstrap_cameras(self):
        """Load cameras from control plane and/or env overrides."""
        cameras: list[dict] = []
        try:
            cameras = self.client.get_cameras()
        except Exception as exc:
            logger.warning("Could not fetch cameras from API: %s", exc)

        # Env explicit sources take priority for local testing
        if self.config.camera_sources:
            for src in self.config.camera_sources:
                cam_id = src.get("camera_id") or (cameras[0]["id"] if cameras else "local-cam")
                if not src.get("camera_id") and cameras:
                    cam_id = cameras[0]["id"]
                self._register_camera(
                    camera_id=cam_id,
                    source=src["source"],
                    name=src.get("name") or "local",
                    zones=[],
                    enabled_modules=["multi_person_tracking", "intrusion_detection"],
                    safety_config=(cameras[0].get("safety_config") if cameras else {}),
                )
            return

        for cam in cameras:
            source = (cam.get("rtsp_url") or "").strip()
            if not source:
                logger.info("Skipping camera without RTSP URL: %s", cam.get("name"))
                continue
            zones = []
            # Zone detail may not be embedded; use empty until API enriched
            self._register_camera(
                camera_id=cam["id"],
                source=source,
                name=cam.get("name") or cam["id"],
                zones=zones,
                enabled_modules=cam.get("enabled_modules") or [],
                safety_config=cam.get("safety_config") or {},
            )

        if not self.streams.camera_ids:
            logger.warning("No RTSP cameras registered; pipeline will idle until sources exist")

    def _register_camera(
        self,
        camera_id: str,
        source: str,
        name: str,
        zones: list[ZoneConfig],
        enabled_modules: list[str],
        safety_config: dict[str, Any] | None = None,
    ):
        self.streams.add_camera(
            camera_id=camera_id,
            source=source,
            name=name,
            queue_size=self.config.frame_queue_size,
            reconnect_delay=self.config.reconnect_delay_sec,
            reconnect_max_delay=self.config.reconnect_max_delay_sec,
            target_fps=self.config.target_infer_fps,
        )
        self.trackers[camera_id] = IOUTracker()
        self.zone_engines[camera_id] = ZoneEngine(
            zones=zones,
            loitering_seconds=self.config.loitering_seconds,
        )
        self.object_trackers[camera_id] = ObjectStateTracker(
            left_seconds=self.config.object_left_seconds,
        )
        self.safety_analyzers[camera_id] = SafetyAnalyzer(safety_config)
        self.evidence_buffers[camera_id] = EvidenceBuffer(
            seconds=self.config.safety_evidence_seconds,
            fps=self.config.target_infer_fps,
        )
        self.track_identities[camera_id] = {}
        if self.config.enable_face:
            self.face_detectors[camera_id] = FaceDetector(
                min_blur=self.config.face_min_blur,
                min_quality=self.config.face_min_quality,
            )
        self._camera_meta[camera_id] = {
            "name": name,
            "source": source,
            "enabled_modules": enabled_modules,
            "safety_config": safety_config or {},
        }
        logger.info("Registered camera %s source=%s", name, source)

    def set_zones_for_camera(self, camera_id: str, zones: list[ZoneConfig]):
        engine = self.zone_engines.get(camera_id)
        if engine:
            engine.set_zones(zones)

    def process_once(self) -> int:
        """Process latest frames from all cameras. Returns events sent count."""
        sent = 0
        for packet in self.streams.iter_latest():
            sent += self._process_packet(packet)
        return sent

    def _process_packet(self, packet) -> int:
        self.stats["frames_processed"] += 1
        detections = self.detector.detect(packet.frame)
        self.stats["detections"] += len(detections)
        evidence = self.evidence_buffers.setdefault(
            packet.camera_id,
            EvidenceBuffer(
                seconds=self.config.safety_evidence_seconds,
                fps=self.config.target_infer_fps,
            ),
        )
        evidence.add(packet.frame)

        tracker = self.trackers.setdefault(packet.camera_id, IOUTracker())
        person_detections = [
            detection
            for detection in detections
            if detection.class_name.lower() == "person"
            or (
                detection.class_name.isdigit()
                and detection.class_id == self.config.person_class_id
            )
        ]
        tracks = tracker.update(person_detections, now=packet.timestamp)
        for track in tracks:
            track.metadata["normalized_centroid"] = track.bbox.normalized_centroid(
                packet.width, packet.height
            )

        events_to_send: list[dict] = []
        modules = self._camera_meta.get(packet.camera_id, {}).get("enabled_modules") or []

        # Always emit person_detected for new/updated tracks (cooldown gated)
        for track in tracks:
            if self.cooldown.allow(packet.camera_id, "person_detected", track.track_id):
                evt = build_person_event(
                    packet.camera_id,
                    track,
                    self.detector.model_name,
                    self.detector.model_version,
                )
                if self.config.enable_snapshots:
                    snap = save_snapshot(packet, track, self.config.snapshot_dir)
                    if snap:
                        evt["payload"]["snapshot"] = snap
                events_to_send.append(evt)

        # Zone evaluation when intrusion / tracking modules enabled
        zone_engine = self.zone_engines.setdefault(
            packet.camera_id,
            ZoneEngine(loitering_seconds=self.config.loitering_seconds),
        )
        zone_events = zone_engine.evaluate(tracks, packet.width, packet.height, now=packet.timestamp)
        for ze in zone_events:
            if self.cooldown.allow(packet.camera_id, ze.event_type, ze.track_id, ze.zone_id):
                evt = build_zone_event(
                    packet.camera_id,
                    ze,
                    self.detector.model_name,
                    self.detector.model_version,
                )
                evt["payload"]["m4"] = True
                if self.config.enable_snapshots:
                    track = next((t for t in tracks if t.track_id == ze.track_id), None)
                    snap = save_snapshot(packet, track, self.config.snapshot_dir)
                    if snap:
                        evt["payload"]["snapshot"] = snap
                events_to_send.append(evt)

        # Crowd analytics
        for snap, should_emit in self.crowd.analyze(
            tracks, packet.width, packet.height, zone_engine.zones, packet.timestamp
        ):
            if not should_emit:
                continue
            if not self.cooldown.allow(packet.camera_id, "crowd", None, snap.zone_id):
                continue
            events_to_send.append(
                {
                    "camera_id": packet.camera_id,
                    "event_type": "crowd",
                    "severity": "critical" if snap.over_capacity else "info",
                    "confidence": 1.0,
                    "model_name": self.detector.model_name,
                    "model_version": self.detector.model_version,
                    "zone_id": snap.zone_id if snap.zone_id != "full" else None,
                    "payload": {
                        "occupancy": snap.occupancy,
                        "max_occupancy": snap.max_occupancy,
                        "density": snap.density,
                        "over_capacity": snap.over_capacity,
                        "heatmap": snap.heatmap,
                        "zone_name": snap.zone_name,
                        "m4": True,
                    },
                    "edge_event_id": __import__("uuid").uuid4().hex,
                }
            )
            self.stats["crowd_events"] += 1

        # Object left / removed
        obj_tracker = self.object_trackers.setdefault(
            packet.camera_id,
            ObjectStateTracker(left_seconds=self.config.object_left_seconds),
        )
        for oe in obj_tracker.update(detections, now=packet.timestamp):
            if not self.cooldown.allow(packet.camera_id, oe.event_type, oe.track_id):
                continue
            events_to_send.append(
                {
                    "camera_id": packet.camera_id,
                    "event_type": oe.event_type,
                    "severity": oe.severity,
                    "confidence": float(oe.confidence),
                    "model_name": self.detector.model_name,
                    "model_version": self.detector.model_version,
                    "payload": {
                        "track_id": oe.track_id,
                        "object_class": oe.object_class,
                        "dwell_seconds": oe.dwell_seconds,
                        **oe.payload,
                        "m4": True,
                    },
                    "edge_event_id": __import__("uuid").uuid4().hex,
                }
            )
            self.stats["object_events"] += 1

        # M5 life safety: custom-model labels + temporal verification.
        safety = self.safety_analyzers.setdefault(packet.camera_id, SafetyAnalyzer())
        identity_context = self.track_identities.setdefault(packet.camera_id, {})
        safety_signals = (
            safety.analyze(
                packet.frame,
                detections,
                tracks,
                packet.timestamp,
                zones=zone_engine.zones,
                person_context=identity_context,
            )
            if self.config.enable_safety
            else []
        )
        for signal in safety_signals:
            cooldown_scope = signal.zone_id
            if signal.event_type == "smoke" and signal.payload.get("persistent"):
                cooldown_scope = "persistent"
            if not self.cooldown.allow(
                packet.camera_id,
                signal.event_type,
                signal.track_id,
                cooldown_scope,
            ):
                continue
            payload = {**signal.payload, "track_id": signal.track_id, "m5": True}
            track = next((item for item in tracks if item.track_id == signal.track_id), None)
            if self.config.enable_snapshots:
                snapshot = save_snapshot(packet, track, self.config.snapshot_dir)
                if snapshot:
                    payload["snapshot"] = snapshot
            if self.config.enable_safety_evidence and signal.severity in {"critical", "emergency"}:
                clip = evidence.save(
                    self.config.snapshot_dir,
                    packet.camera_id,
                    signal.event_type,
                )
                if clip:
                    payload["evidence_clip"] = clip
            events_to_send.append(
                {
                    "camera_id": packet.camera_id,
                    "event_type": signal.event_type,
                    "severity": signal.severity,
                    "confidence": float(signal.confidence),
                    "model_name": self.detector.model_name,
                    "model_version": self.detector.model_version,
                    "zone_id": signal.zone_id,
                    "payload": payload,
                    "edge_event_id": __import__("uuid").uuid4().hex,
                }
            )
            self.stats["safety_events"] += 1

        # M3 face recognition
        if self.config.enable_face and self.face_embedder is not None:
            face_det = self.face_detectors.setdefault(
                packet.camera_id,
                FaceDetector(min_blur=self.config.face_min_blur, min_quality=self.config.face_min_quality),
            )
            for track in tracks:
                if not self.cooldown.allow(packet.camera_id, "face_match", track.track_id):
                    continue
                crop = face_det.detect_on_track(packet.frame, track)
                if crop is None:
                    continue
                embedding = self.face_embedder.embed(crop.image)
                try:
                    result = self.client.face_match(
                        {
                            "camera_id": packet.camera_id,
                            "embedding": embedding,
                            "threshold": self.config.face_match_threshold,
                            "track_id": track.track_id,
                            "confidence": crop.quality_score,
                            "create_attendance": True,
                            "create_unknown_if_miss": True,
                        }
                    )
                    if result.get("match"):
                        identity_context[track.track_id] = {
                            "person_id": result.get("person_id"),
                            "person_type": result.get("person_type"),
                            "full_name": result.get("full_name"),
                        }
                        self.stats["faces_matched"] += 1
                        logger.info(
                            "Face match %s (%s) score=%.2f",
                            result.get("full_name"),
                            result.get("person_type"),
                            result.get("score", 0),
                        )
                    else:
                        self.stats["faces_unknown"] += 1
                        logger.info("Unknown face track=%s score=%.2f", track.track_id, result.get("score", 0))
                except Exception as exc:
                    logger.error("Face match failed: %s", exc)

        sent = 0
        for evt in events_to_send:
            try:
                self.client.ingest_event(evt)
                sent += 1
                self.stats["events_sent"] += 1
                logger.info(
                    "Event %s camera=%s track=%s conf=%.2f",
                    evt["event_type"],
                    packet.camera_name,
                    evt["payload"].get("track_id"),
                    evt["confidence"],
                )
            except Exception as exc:
                self.stats["events_failed"] += 1
                logger.error("Ingest failed: %s", exc)
        return sent

    def health_metadata(self) -> dict:
        return {
            "service": "edge-ai",
            "mode": "m5-pipeline",
            "detector": self.detector.model_name,
            "detector_version": self.detector.model_version,
            "face_enabled": self.config.enable_face,
            "face_model": self.face_embedder.model_name if self.face_embedder else None,
            "crowd_enabled": True,
            "object_tracking": True,
            "safety_enabled": self.config.enable_safety,
            "safety_evidence": self.config.enable_safety_evidence,
            "cameras": [
                {
                    "camera_id": h.camera_id,
                    "connected": h.connected,
                    "fps": round(h.fps, 2),
                    "frames_read": h.frames_read,
                    "reconnect_count": h.reconnect_count,
                    "last_error": h.last_error,
                }
                for h in self.streams.all_health()
            ],
            "stats": self.stats,
        }

    def stop(self):
        self.streams.stop_all()

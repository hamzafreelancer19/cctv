"""SentinelVision Edge AI Service — M2 RTSP / YOLO / tracking / zones pipeline."""

from __future__ import annotations

import logging
import signal
import sys
import time

from edge_service.client import ControlPlaneClient
from edge_service.config import EdgeConfig
from edge_service.inference import SimulatedYOLODetector, build_event_payload
from edge_service.pipeline import DetectionPipeline
from edge_service.zones.engine import ZoneConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("edge-service")


class EdgeService:
    def __init__(self, config: EdgeConfig):
        self.config = config
        self.client = ControlPlaneClient(config.api_base_url, config.edge_api_key)
        self.running = True
        self.pipeline: DetectionPipeline | None = None
        self._sim_detector = SimulatedYOLODetector()
        self.camera_id = config.camera_id

    def _use_simulation(self) -> bool:
        if self.config.mode == "simulation":
            return True
        if self.config.mode == "rtsp":
            return False
        # auto: simulation if no RTSP/video sources and no cameras with rtsp after bootstrap attempt
        return False

    def bootstrap(self):
        self.pipeline = DetectionPipeline(self.config, self.client)
        self.pipeline.bootstrap_cameras()
        self._hydrate_zones_from_api()
        if not self.pipeline.streams.camera_ids and self.config.mode != "rtsp":
            logger.info("No live sources found — falling back to simulation mode")
            self.config.mode = "simulation"

    def _hydrate_zones_from_api(self):
        if not self.pipeline:
            return
        try:
            cameras = self.client.get_cameras()
        except Exception as exc:
            logger.warning("Zone hydrate failed: %s", exc)
            return
        for cam in cameras:
            cam_id = cam.get("id")
            if not cam_id or cam_id not in self.pipeline.zone_engines:
                continue
            analyzer = self.pipeline.safety_analyzers.get(cam_id)
            if analyzer:
                analyzer.set_profile(cam.get("safety_config") or {})
            zones = []
            for z in cam.get("site_zones") or []:
                if not z.get("is_active", True):
                    continue
                zones.append(
                    ZoneConfig(
                        zone_id=str(z["id"]),
                        name=z.get("name") or "zone",
                        polygon=z.get("polygon_json") or [],
                        is_restricted=bool(z.get("is_restricted")),
                        loitering_seconds=float(z.get("loitering_seconds") or self.config.loitering_seconds),
                        visitor_loitering_seconds=float(z.get("visitor_loitering_seconds") or 60),
                        ignore_employees=bool(z.get("ignore_employees")),
                        priority=z.get("priority") or "medium",
                        max_occupancy=z.get("max_occupancy"),
                        access_start=z.get("access_start"),
                        access_end=z.get("access_end"),
                        after_hours_restricted=bool(z.get("after_hours_restricted", True)),
                        entry_line=z.get("entry_line_json") or [],
                    )
                )
            # Also include camera-linked zone if present
            if cam.get("zone") and cam.get("zone_polygon"):
                zones.append(
                    ZoneConfig(
                        zone_id=str(cam["zone"]),
                        name=cam.get("zone_name") or "camera-zone",
                        polygon=cam.get("zone_polygon") or [],
                        is_restricted=bool(cam.get("zone_is_restricted")),
                        loitering_seconds=self.config.loitering_seconds,
                    )
                )
            # de-dupe by zone_id
            unique = {z.zone_id: z for z in zones}
            self.pipeline.set_zones_for_camera(cam_id, list(unique.values()))
            if unique:
                logger.info("Loaded %s zones for camera %s", len(unique), cam.get("name"))

    def send_heartbeat(self):
        metadata = {"service": "edge-ai", "mode": self.config.mode}
        if self.pipeline:
            metadata.update(self.pipeline.health_metadata())
        try:
            result = self.client.heartbeat(version=self.config.version, metadata=metadata)
            logger.info("Heartbeat OK: registered=%s", result.get("registered"))
        except Exception as exc:
            logger.error("Heartbeat failed: %s", exc)

    def run_simulation_cycle(self):
        camera_id = self.camera_id
        if not camera_id and self.pipeline and self.pipeline.streams.camera_ids:
            camera_id = self.pipeline.streams.camera_ids[0]
        if not camera_id:
            try:
                cameras = self.client.get_cameras()
                if cameras:
                    camera_id = cameras[0]["id"]
                    self.camera_id = camera_id
            except Exception as exc:
                logger.warning("Simulation camera resolve failed: %s", exc)
                return
        if not camera_id:
            logger.warning("No camera for simulation")
            return
        for det in self._sim_detector.detect():
            event = build_event_payload(camera_id, det)
            try:
                result = self.client.ingest_event(event)
                logger.info("Sim event %s conf=%.2f", result.get("id"), det.confidence)
            except Exception as exc:
                logger.error("Sim ingest failed: %s", exc)

    def run(self):
        logger.info("Starting SentinelVision Edge Service v%s", self.config.version)
        logger.info("Control plane: %s mode=%s backend=%s", self.config.api_base_url, self.config.mode, self.config.detection_backend)
        self.bootstrap()

        last_heartbeat = 0.0
        last_sim = 0.0
        while self.running:
            now = time.time()
            if now - last_heartbeat >= self.config.heartbeat_interval:
                self.send_heartbeat()
                last_heartbeat = now

            if self.config.mode == "simulation" or (self.pipeline and not self.pipeline.streams.camera_ids):
                if now - last_sim >= self.config.simulation_interval:
                    self.run_simulation_cycle()
                    last_sim = now
                time.sleep(0.5)
            else:
                assert self.pipeline is not None
                self.pipeline.process_once()
                time.sleep(0.05)

        if self.pipeline:
            self.pipeline.stop()
        self.client.close()
        logger.info("Edge service stopped")

    def stop(self, *_args):
        self.running = False


def main():
    config = EdgeConfig.from_env()
    service = EdgeService(config)
    signal.signal(signal.SIGINT, service.stop)
    signal.signal(signal.SIGTERM, service.stop)
    try:
        service.run()
    except KeyboardInterrupt:
        service.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()

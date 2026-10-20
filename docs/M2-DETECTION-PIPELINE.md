# M2 — Detection Pipeline

Modular edge pipeline delivering RTSP (or video) → YOLO → tracking → zones → events → dashboard.

## Architecture

```
RTSP / Video Source
        │
        ▼
 Stream Manager (reconnect, FPS, frame queue)
        │
        ▼
 YOLO Detector (ultralytics or simulated fallback)
        │
        ▼
 IoU Tracker (persistent track IDs)
        │
        ▼
 Zone Engine (intrusion, loitering)
        │
        ▼
 Event Builder + cooldown
        │
        ▼
 Control Plane POST /api/v1/events/ingest/
        │
        ▼
 Alert rules → Dashboard (auto-refresh)
```

## Edge modules

| Module | Path |
|--------|------|
| Config | `edge/edge_service/config.py` |
| RTSP/Stream | `edge/edge_service/rtsp/stream_manager.py` |
| YOLO | `edge/edge_service/yolo/detector.py` |
| Tracker | `edge/edge_service/tracker/iou_tracker.py` |
| Zones | `edge/edge_service/zones/engine.py` |
| Events | `edge/edge_service/events/builder.py` |
| Pipeline | `edge/edge_service/pipeline.py` |
| Main | `edge/edge_service/main.py` |

## Modes

| `EDGE_MODE` | Behavior |
|-------------|----------|
| `auto` | Use RTSP/VIDEO_SOURCE or API cameras; else simulation |
| `rtsp` | Require live sources |
| `simulation` | Legacy random person events (no OpenCV stream) |

| `DETECTION_BACKEND` | Behavior |
|---------------------|----------|
| `simulated` | No YOLO weights required (default for CI/dev) |
| `yolo` | Requires `ultralytics` + model file |
| `auto` | Try YOLO, fall back to simulated |

## Run with live RTSP

```bash
cd edge
cp .env.example .env
# edit:
# EDGE_MODE=rtsp
# DETECTION_BACKEND=yolo   # or simulated
# RTSP_URL=rtsp://user:pass@camera/stream
# CAMERA_ID=<uuid from API>
pip install -r requirements.txt
# optional real YOLO:
# pip install ultralytics
python -m edge_service.main
```

## Run with local video / webcam

```bash
EDGE_MODE=rtsp
VIDEO_SOURCE=sample.mp4   # or 0 for webcam
DETECTION_BACKEND=simulated
python -m edge_service.main
```

## Tests

```bash
cd edge
python -m pytest tests/ -q
```

## Sprint coverage

| Sprint | Status |
|--------|--------|
| 1 RTSP foundation | Implemented |
| 2 YOLO service | Implemented (optional ultralytics) |
| 3 Multi-person tracking | Implemented (IoU tracker) |
| 4 Zone engine | Implemented |
| 5 Event pipeline | Implemented |
| 6 Dashboard integration | Implemented (polling + track IDs) |

## Before M3

Stabilize M2 with a real RTSP or video file, tune confidence/cooldown, then add InsightFace on tracked person crops.

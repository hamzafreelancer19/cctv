---
volume: 06
title: AI Design Document
status: draft
---

# AI Design Document

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


## 1. AI Platform Overview

Edge performs stream ingestion and inference; control plane stores metadata, alerts, and evidence references.

**Current state:** SimulatedYOLODetector produces randomized person_detected events for pipeline validation.

## 2. Module Catalog

| ID | Module | Model | Status | Description |
|----|--------|-------|--------|-------------|
| AI-FACE | Face Recognition | InsightFace | Planned | Identify enrolled persons |
| AI-UNKNOWN | Unknown Person Detection | InsightFace + threshold | Planned | Flag non-enrolled faces |
| AI-TRACK | Multi-Person Tracking | YOLO + ByteTrack | Planned | Maintain track IDs |
| AI-INTR | Intrusion Detection | YOLO + zone rules | Planned | Restricted zone entry |
| AI-ACT | Activity Recognition | YOLO-Pose | Future | Loitering, fall, fight |
| AI-FIRE | Fire Detection | Custom YOLO | Future | Visual flame cues |
| AI-SMOKE | Smoke Detection | Custom YOLO | Future | Visual smoke cues |
| AI-WEAPON | Weapon Detection | Custom YOLO | Future | Firearms/knives |
| AI-ATT | Attendance | Face + rules | Planned | Clock-in/out |
| AI-VIS | Visitor Management | Face + registry | Planned | Match pre-registered visitors |
| AI-VEH | Vehicle Detection | YOLO | Future | Vehicle class detection |
| AI-LPR | License Plate Recognition | OCR + detector | Future | Plate text extraction |

## 3. Shared Pipeline

```
RTSP -> FrameSampler -> Detector -> Tracker -> ModuleRouter -> EventBuilder -> LocalQueue -> HTTPS
```

## 4. Module Template

Each module specification includes:
- Input/output contract
- Dataset requirements and licensing
- Model selection criteria
- Confidence thresholds
- Training and evaluation metrics
- Inference flow
- GPU optimization notes
- Versioning and rollback
- Privacy and bias controls

## 5. AI-FACE — Face Recognition

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Model | InsightFace (buffalo_l or production equivalent) |
| Input | Face crop 112x112+ |
| Output | person_id, confidence, embedding |
| Threshold | 0.75 default; review below 0.85 |
| GPU | Batch inference every N frames |
| Privacy | Requires BiometricConsent record |
| Metrics | TAR@FAR 1e-3 on validation set |

**Inference flow:**
1. YOLO person detection
2. Face landmark detection
3. Embedding extraction
4. Nearest neighbor against gallery
5. Emit face_recognized or unknown_person

## 6. AI-INTR — Intrusion Detection

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Input | Track centroid + zone polygon |
| Rule | Person enters restricted zone during active schedule |
| Output | intrusion event, severity warning/critical |
| Threshold | detection confidence >= 0.6 |

## 7. AI-WEAPON — Weapon Detection

| Attribute | Value |
|-----------|-------|
| Status | Future |
| Model | Custom YOLO trained on weapon datasets |
| Output | weapon event, critical severity |
| Threshold | 0.70 minimum before alert |
| Human review | Mandatory before escalation |

## 8. AI-ATT — Attendance

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Input | face_recognized at entry camera |
| Business rules | One check-in per person per day before cutoff |
| Output | attendance record linked to person profile |

## 9. Dataset Governance

| Requirement | Policy |
|-------------|--------|
| Licensing | Commercial-use approved datasets only |
| PII | Anonymize training exports |
| Bias | Evaluate across age/gender/skin tone buckets |
| Retention | Training snapshots deleted after model promotion |

## 10. Model Versioning

| Field | Storage |
|-------|---------|
| model_name | DetectionEvent.model_name |
| model_version | DetectionEvent.model_version |
| registry | Planned ai_modelregistry table |
| rollback | Edge OTA package pin to previous version |

## 11. GPU Optimization

- FP16 inference where supported
- Frame skipping adaptive to GPU load
- Batch face embedding extraction
- Limit concurrent RTSP decodes to hardware capacity

## 12. Performance Metrics

| Module | Precision Target | Recall Target | FPS Target |
|--------|------------------|---------------|------------|
| Person detection | 0.90 | 0.88 | 15+ @1080p |
| Face recognition | 0.95 | 0.90 | 10+ |
| Intrusion | 0.92 | 0.90 | N/A rule-based |
| Weapon | 0.85 | 0.80 | 10+ |

## 13. Current Simulation

SimulatedYOLODetector emits person_detected with random confidence and bbox for integration testing only. Not for production security decisions.

"""SIEM event forwarders."""

from __future__ import annotations

import json
import logging
import socket
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def build_siem_payload(event) -> dict[str, Any]:
    return {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "camera_id": str(event.camera_id),
        "camera_name": event.camera.name,
        "site": event.camera.site.name,
        "organization": event.organization.name,
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
        "source": "sentinelvision",
    }


def forward_to_siem(target: str, destination: str, payload: dict) -> tuple[bool, str]:
    target = (target or "webhook").lower()
    try:
        if target in {"webhook", "splunk", "sentinel", "qradar", "elastic"}:
            if destination.startswith("/"):
                return True, json.dumps({"stub": True, "target": target, "path": destination})
            headers = {"Content-Type": "application/json"}
            if target == "splunk":
                headers["Authorization"] = f"Splunk {getattr(settings, 'SPLUNK_HEC_TOKEN', 'dev-token')}"
            response = requests.post(
                destination,
                json=payload if target != "splunk" else {"event": payload},
                headers=headers,
                timeout=getattr(settings, "WEBHOOK_DEFAULT_TIMEOUT_SEC", 10),
            )
            if response.status_code >= 400:
                return False, f"HTTP {response.status_code}: {response.text[:500]}"
            return True, response.text[:500]
        if target == "syslog":
            host, _, port = destination.partition(":")
            port_i = int(port or "514")
            message = f"<134>sentinelvision: {json.dumps(payload)}\n"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message.encode("utf-8"), (host, port_i))
            sock.close()
            return True, "syslog_sent"
        return False, f"Unknown SIEM target: {target}"
    except Exception as exc:
        logger.exception("SIEM forward failed")
        return False, str(exc)

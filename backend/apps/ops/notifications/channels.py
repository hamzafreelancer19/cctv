"""Channel adapters for email/SMS/WhatsApp/push/webhook."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class DeliveryResult:
    def __init__(self, success: bool, response: str = "", latency_ms: int = 0, error: str = ""):
        self.success = success
        self.response = response
        self.latency_ms = latency_ms
        self.error = error


def deliver_channel(channel: str, destination: str, subject: str, body: str, payload: dict | None = None) -> DeliveryResult:
    started = time.perf_counter()
    payload = payload or {}
    try:
        if channel == "email":
            result = _email(destination, subject, body)
        elif channel == "sms":
            result = _http_provider(settings.SMS_PROVIDER_URL, destination, subject, body, payload, "sms")
        elif channel == "whatsapp":
            result = _http_provider(settings.WHATSAPP_PROVIDER_URL, destination, subject, body, payload, "whatsapp")
        elif channel == "push":
            result = _http_provider(settings.PUSH_PROVIDER_URL, destination, subject, body, payload, "push")
        elif channel == "webhook":
            result = _webhook(destination, subject, body, payload)
        else:
            return DeliveryResult(False, error=f"Unknown channel: {channel}")
        latency = int((time.perf_counter() - started) * 1000)
        result.latency_ms = latency
        return result
    except Exception as exc:
        latency = int((time.perf_counter() - started) * 1000)
        logger.exception("Notification delivery failed channel=%s", channel)
        return DeliveryResult(False, latency_ms=latency, error=str(exc))


def _email(destination: str, subject: str, body: str) -> DeliveryResult:
    if not destination:
        return DeliveryResult(False, error="Missing email destination")
    count = send_mail(
        subject=subject or "SentinelVision Alert",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destination],
        fail_silently=False,
    )
    return DeliveryResult(True, response=f"sent={count}")


def _webhook(destination: str, subject: str, body: str, payload: dict) -> DeliveryResult:
    if not destination:
        return DeliveryResult(False, error="Missing webhook destination")
    # Relative destinations are treated as local ops stubs.
    if destination.startswith("/"):
        return DeliveryResult(True, response=json.dumps({"stub": True, "path": destination}))
    data = {"subject": subject, "body": body, "payload": payload}
    response = requests.post(
        destination,
        json=data,
        timeout=settings.WEBHOOK_DEFAULT_TIMEOUT_SEC,
    )
    if response.status_code >= 400:
        return DeliveryResult(False, response=response.text[:1000], error=f"HTTP {response.status_code}")
    return DeliveryResult(True, response=response.text[:1000])


def _http_provider(
    url: str,
    destination: str,
    subject: str,
    body: str,
    payload: dict,
    kind: str,
) -> DeliveryResult:
    if not url:
        # Dev-friendly stub when provider URL is not configured.
        logger.info("Stub %s notification to %s: %s", kind, destination, subject)
        return DeliveryResult(True, response=json.dumps({"stub": True, "channel": kind, "to": destination}))
    response = requests.post(
        url,
        json={"to": destination, "subject": subject, "body": body, "payload": payload},
        timeout=settings.WEBHOOK_DEFAULT_TIMEOUT_SEC,
    )
    if response.status_code >= 400:
        return DeliveryResult(False, response=response.text[:1000], error=f"HTTP {response.status_code}")
    return DeliveryResult(True, response=response.text[:1000])

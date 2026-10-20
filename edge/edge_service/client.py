"""HTTP client for control plane communication with retry support."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ControlPlaneClient:
    def __init__(self, base_url: str, api_key: str, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self._client = httpx.Client(
            headers={"X-Edge-API-Key": api_key, "Content-Type": "application/json"},
            timeout=30.0,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.request(method, url, **kwargs)
                if response.status_code >= 500 and attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return response
            except httpx.RequestError as exc:
                last_exc = exc
                logger.warning("Request failed (attempt %s): %s", attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise last_exc or RuntimeError("Request failed")

    def heartbeat(self, version: str, metadata: dict | None = None) -> dict:
        payload = {"version": version, "status": "online", "metadata": metadata or {}}
        response = self._request("POST", "/edge/heartbeat/", json=payload)
        response.raise_for_status()
        return response.json()

    def ingest_event(self, event: dict[str, Any]) -> dict:
        response = self._request("POST", "/events/ingest/", json=event)
        response.raise_for_status()
        return response.json()

    def get_cameras(self) -> list[dict]:
        response = self._request("GET", "/edge/cameras/")
        response.raise_for_status()
        return response.json().get("results", [])

    def get_face_gallery(self, organization_id: str | None = None) -> list[dict]:
        params = {}
        if organization_id:
            params["organization_id"] = organization_id
        response = self._request("GET", "/face/gallery/", params=params)
        response.raise_for_status()
        return response.json().get("results", [])

    def face_match(self, payload: dict[str, Any]) -> dict:
        response = self._request("POST", "/face/match/", json=payload)
        response.raise_for_status()
        return response.json()

    def close(self):
        self._client.close()

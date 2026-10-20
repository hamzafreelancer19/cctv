"""Celery tasks for continuous camera monitoring."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.cameras.tasks.monitor_cameras_tick")
def monitor_cameras_tick():
    """Periodic backend tick so capture continues without the Cameras page open."""
    from apps.cameras.monitor import monitor_active_cameras

    result = monitor_active_cameras(run_vision=True)
    logger.debug(
        "Camera monitor tick: checked=%s ok=%s",
        result.get("checked"),
        result.get("ok"),
    )
    return result

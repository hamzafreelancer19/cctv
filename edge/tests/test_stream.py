"""M2 stream manager tests (no live camera required)."""

from edge_service.rtsp.stream_manager import StreamManager
from edge_service.types import StreamHealth


def test_stream_manager_empty_health():
    mgr = StreamManager()
    assert mgr.all_health() == []
    assert mgr.iter_latest() == []
    mgr.stop_all()


def test_stream_health_defaults():
    h = StreamHealth(camera_id="c1", source="rtsp://x", connected=False)
    assert h.fps == 0.0
    assert h.reconnect_count == 0

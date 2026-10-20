"""Open an RTSP capture with TCP transport.

OpenCV only reads OPENCV_FFMPEG_CAPTURE_OPTIONS at import time. Docker's NAT
drops UDP RTP, so the option has to be set before cv2 loads or the stream hangs.
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|stimeout;8000000|rw_timeout;8000000|max_delay;500000",
)

import cv2

def open_rtsp_capture(url: str):
    """Return a VideoCapture. Caller must release it.

    Do not pass CAP_PROP_* params into VideoCapture(). This OpenCV build rejects
    them and then refuses to open the stream at all. Timeouts come from
    OPENCV_FFMPEG_CAPTURE_OPTIONS, which is set before cv2 is imported.
    """
    if hasattr(cv2, "CAP_FFMPEG"):
        return cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    return cv2.VideoCapture(url)

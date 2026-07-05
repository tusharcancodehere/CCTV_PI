"""Camera module."""

from camera.manager import camera_manager
from camera.detectors import DetectorManager
from camera.stream import StreamGenerator
from camera.recorder import VideoRecorder
from camera.snapshots import SnapshotCapture

__all__ = [
    "camera_manager",
    "DetectorManager",
    "StreamGenerator",
    "VideoRecorder",
    "SnapshotCapture",
]

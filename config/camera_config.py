"""Unified configuration model."""

class CameraConfig:
    resolution = (1280, 720)
    fps = 30
    max_fps = 60
    min_fps = 15
    jpeg_quality = 70
    mode = "balanced"  # performance | balanced | quality

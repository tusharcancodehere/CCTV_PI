"""Configuration management for OpenCV Vision Dashboard."""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


def is_raspberry_pi() -> bool:
    """Check if the system is a Raspberry Pi."""
    try:
        model_path = Path("/proc/device-tree/model")
        if model_path.exists():
            model = model_path.read_text().lower()
            return "raspberry pi" in model
    except Exception:
        pass
    return False


class CameraBackend(Enum):
    """Supported camera backends."""
    OPENCV = "opencv"
    PICAMERA2 = "picamera2"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8888
    DEBUG: bool = False
    
    # Camera
    CAMERA_BACKEND: CameraBackend = CameraBackend.OPENCV
    CAMERA_RESOLUTION: tuple = (1280, 720)
    CAMERA_FPS: int = 30
    CAMERA_BUFFER_SIZE: int = 2
    
    # Recording
    RECORDING_BITRATE: str = "2000k"  # Low bitrate for Pi
    RECORDING_CODEC: str = "libx264"
    RECORDING_PRESET: str = "ultrafast"  # For low CPU
    
    # Streaming
    MJPEG_QUALITY: int = 80
    MJPEG_BUFFER_SIZE: int = 1
    STREAMING_FPS: int = 30
    MIRROR_PREVIEW: bool = True

    
    # Analytics
    ANALYTICS_BUFFER_SIZE: int = 60
    ANALYTICS_UPDATE_INTERVAL: int = 1  # seconds
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent
    LOGS_DIR: Path = BASE_DIR / "logs"
    RECORDINGS_DIR: Path = BASE_DIR / "recordings"
    SNAPSHOTS_DIR: Path = BASE_DIR / "snapshots"
    CACHE_DIR: Path = BASE_DIR / "cache"
    
    # Feature Flags
    ENABLE_MOTION_DETECTION: bool = True
    ENABLE_FACE_DETECTION: bool = True
    ENABLE_QR_DETECTION: bool = True
    ENABLE_AI_MODULES: bool = False  # Disabled by default for low RAM
    
    # Performance
    LOG_LEVEL: LogLevel = LogLevel.INFO
    MAX_LOG_ENTRIES: int = 100
    FRAME_RESIZE_WIDTH: int = 640  # Internal resize for processing
    ENABLE_FRAME_SKIP: bool = True  # Skip frames on low RAM
    
    def __post_init__(self) -> None:
        """Create required directories and auto-tune for Raspberry Pi."""
        for directory in [self.LOGS_DIR, self.RECORDINGS_DIR, 
                          self.SNAPSHOTS_DIR, self.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            
        if is_raspberry_pi():
            self.CAMERA_RESOLUTION = (640, 480)
            self.CAMERA_FPS = 15
            self.STREAMING_FPS = 15
            self.ENABLE_MOTION_DETECTION = True
            self.ENABLE_FACE_DETECTION = False
            self.ENABLE_QR_DETECTION = False
            self.FRAME_RESIZE_WIDTH = 320
            self.MJPEG_QUALITY = 80


# Global config instance
config = AppConfig()

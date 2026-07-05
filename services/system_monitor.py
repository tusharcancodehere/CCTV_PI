"""System monitoring service."""

import platform
import socket
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import psutil
import cv2

from config import config, CameraBackend


@dataclass
class SystemStats:
    """System statistics snapshot."""
    timestamp: datetime
    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    ram_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    temperature_c: Optional[float]
    hostname: str
    ip_address: str
    python_version: str
    opencv_version: str
    operating_system: str
    platform_arch: str
    camera_backend: str
    camera_connected: bool
    camera_resolution: tuple
    current_fps: float
    frame_count: int
    uptime_seconds: float
    recording_status: bool


class SystemMonitor:
    """Monitors system resources."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self.start_time = datetime.now()
        self.frame_count = 0
        self.last_fps = 30.0
        self.recording = False
    
    def get_cpu_percent(self) -> float:
        """Get CPU usage percentage (non-blocking)."""
        return psutil.cpu_percent(interval=None)
    
    def get_ram_info(self) -> tuple:
        """Get RAM usage (percent, used_mb, total_mb)."""
        try:
            mem = psutil.virtual_memory()
            return (
                mem.percent,
                mem.used / (1024 * 1024),
                mem.total / (1024 * 1024)
            )
        except Exception:
            return 0.0, 0.0, 0.0
    
    def get_disk_info(self) -> tuple:
        """Get disk usage (percent, used_gb, total_gb)."""
        try:
            disk = psutil.disk_usage("/")
            return (
                disk.percent,
                disk.used / (1024**3),
                disk.total / (1024**3)
            )
        except Exception:
            return 0.0, 0.0, 0.0
    
    def get_temperature(self) -> Optional[float]:
        """Get system temperature in Celsius."""
        try:
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                return temps["coretemp"][0].current
            elif "cpu_thermal" in temps:
                return temps["cpu_thermal"][0].current
            return None
        except Exception:
            return None
    
    def get_hostname(self) -> str:
        """Get system hostname."""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    def get_ip_address(self) -> str:
        """Get system IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "N/A"
    
    def get_python_version(self) -> str:
        """Get Python version."""
        try:
            return platform.python_version()
        except Exception:
            return "unknown"
    
    def get_opencv_version(self) -> str:
        """Get OpenCV version."""
        try:
            return cv2.__version__
        except Exception:
            return "unknown"
    
    def get_os_info(self) -> tuple:
        """Get OS name and architecture."""
        try:
            return (
                platform.system(),
                platform.machine()
            )
        except Exception:
            return "unknown", "unknown"
    
    def get_uptime(self) -> float:
        """Get uptime in seconds."""
        try:
            return (datetime.now() - self.start_time).total_seconds()
        except Exception:
            return 0.0
    
    def update_frame_count(self, count: int) -> None:
        """Update frame counter."""
        self.frame_count = count
    
    def update_fps(self, fps: float) -> None:
        """Update current FPS."""
        self.last_fps = fps
    
    def set_recording(self, status: bool) -> None:
        """Update recording status."""
        self.recording = status
    
    def get_stats(self, 
                  camera_connected: bool = False,
                  camera_resolution: tuple = (0, 0)) -> SystemStats:
        """Get comprehensive system statistics."""
        cpu_percent = 0.0
        try:
            cpu_percent = self.get_cpu_percent()
        except Exception:
            pass
            
        ram_percent, ram_used, ram_total = self.get_ram_info()
        disk_percent, disk_used, disk_total = self.get_disk_info()
        
        os_name, arch = self.get_os_info()
        
        return SystemStats(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_mb=ram_used,
            ram_total_mb=ram_total,
            disk_percent=disk_percent,
            disk_used_gb=disk_used,
            disk_total_gb=disk_total,
            temperature_c=self.get_temperature(),
            hostname=self.get_hostname(),
            ip_address=self.get_ip_address(),
            python_version=self.get_python_version(),
            opencv_version=self.get_opencv_version(),
            operating_system=os_name,
            platform_arch=arch,
            camera_backend=config.CAMERA_BACKEND.value,
            camera_connected=camera_connected,
            camera_resolution=camera_resolution,
            current_fps=self.last_fps,
            frame_count=self.frame_count,
            uptime_seconds=self.get_uptime(),
            recording_status=self.recording
        )
    
    def to_dict(self, stats: SystemStats) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        data = asdict(stats)
        data["timestamp"] = data["timestamp"].isoformat()
        return data


# Global instance
system_monitor = SystemMonitor()

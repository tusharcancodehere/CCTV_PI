"""Analytics service for historical data tracking (low RAM optimized)."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any
import threading

from config import config
from services.logger import logger_service


@dataclass
class MetricSnapshot:
    """Single metric data point."""
    timestamp: float
    value: float


class MetricsBuffer:
    """Ring buffer for metrics (low RAM friendly)."""
    
    def __init__(self, capacity: int = 60):
        self.capacity = capacity
        self.data: deque = deque(maxlen=capacity)
    
    def add(self, value: float) -> None:
        """Add metric value."""
        self.data.append(MetricSnapshot(
            timestamp=datetime.now().timestamp(),
            value=value
        ))
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all data points."""
        return [
            {"timestamp": s.timestamp, "value": s.value}
            for s in self.data
        ]
    
    def get_average(self) -> float:
        """Get average value."""
        if not self.data:
            return 0.0
        return sum(s.value for s in self.data) / len(self.data)
    
    def get_max(self) -> float:
        """Get maximum value."""
        if not self.data:
            return 0.0
        return max(s.value for s in self.data)
    
    def get_min(self) -> float:
        """Get minimum value."""
        if not self.data:
            return 0.0
        return min(s.value for s in self.data)
    
    def clear(self) -> None:
        """Clear all data."""
        self.data.clear()


class AnalyticsService:
    """Tracks application metrics over time."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        capacity = config.ANALYTICS_BUFFER_SIZE
        
        # Metrics buffers
        self.fps_history = MetricsBuffer(capacity)
        self.cpu_history = MetricsBuffer(capacity)
        self.ram_history = MetricsBuffer(capacity)
        self.temperature_history = MetricsBuffer(capacity)
        
        # Counters
        self.snapshot_count = 0
        self.motion_events = 0
        self.face_detections = 0
        self.qr_detections = 0
        self.camera_restarts = 0
        self.recording_duration = 0.0
        
        # Thread control
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.logger = logger_service.get_logger("analytics")
        
    def start(self) -> None:
        """Start background analytics recording thread."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self.thread = threading.Thread(
                target=self._analytics_loop,
                daemon=True
            )
            self.thread.start()
            self.logger.info("Analytics and Watchdog thread started")
            
    def stop(self) -> None:
        """Stop background analytics recording thread."""
        with self.lock:
            if not self.running:
                return
            self.running = False
            
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
            self.logger.info("Analytics and Watchdog thread stopped")
            
    def _analytics_loop(self) -> None:
        """Periodic background execution: analytics recording, watchdog monitor, and GC."""
        import psutil
        import gc
        import time
        from camera import camera_manager
        
        last_cleanup_time = 0.0
        
        while self.running:
            try:
                # 1. Update stats
                # Using interval=None in psutil.cpu_percent makes it non-blocking
                cpu = psutil.cpu_percent(interval=None)
                ram_percent = psutil.virtual_memory().percent
                
                # Temperature estimation
                temp = None
                try:
                    temps = psutil.sensors_temperatures()
                    if "coretemp" in temps:
                        temp = temps["coretemp"][0].current
                    elif "cpu_thermal" in temps:
                        temp = temps["cpu_thermal"][0].current
                except Exception:
                    pass
                
                self.record_cpu(cpu)
                self.record_ram(ram_percent)
                if temp is not None:
                    self.record_temperature(temp)
                    
                # 2. Watchdog and Auto-reconnection logic
                now = time.time()
                if camera_manager.should_run:
                    if not camera_manager.running:
                        if not hasattr(self, "_last_reconnect_attempt"):
                            self._last_reconnect_attempt = 0.0
                        if now - self._last_reconnect_attempt > 10.0:
                            self.logger.info("Camera was started but is not running. Retrying initialization in background...")
                            self._last_reconnect_attempt = now
                            threading.Thread(target=camera_manager._recover_camera, daemon=True).start()
                    elif camera_manager.running:
                        self.record_fps(camera_manager.fps)
                        
                        with camera_manager.lock:
                            last_update = camera_manager.last_update_time
                            connected = camera_manager.connected
                        
                        if connected and (now - last_update > 5.0):
                            self.logger.warning("Camera stall detected (no frames for 5s) in watchdog. Triggering recovery...")
                            threading.Thread(target=camera_manager._recover_camera, daemon=True).start()
                
                # 4. Storage cleanup once per hour
                now_t = time.time()
                if now_t - last_cleanup_time > 3600.0:
                    try:
                        from services.storage import storage_service
                        storage_service.cleanup_old_files(max_age_days=7)
                    except Exception:
                        pass
                    last_cleanup_time = now_t
                    
                # 5. Trigger garbage collection periodically (every 30 seconds)
                if int(now_t) % 30 == 0:
                    gc.collect()
                    
            except Exception as e:
                self.logger.error(f"Analytics loop error: {e}")
                
            time.sleep(config.ANALYTICS_UPDATE_INTERVAL)
    
    def record_fps(self, fps: float) -> None:
        """Record FPS metric."""
        self.fps_history.add(fps)
    
    def record_cpu(self, cpu_percent: float) -> None:
        """Record CPU metric."""
        self.cpu_history.add(cpu_percent)
    
    def record_ram(self, ram_percent: float) -> None:
        """Record RAM metric."""
        self.ram_history.add(ram_percent)
    
    def record_temperature(self, temp_c: float) -> None:
        """Record temperature metric."""
        self.temperature_history.add(temp_c)
    
    def increment_snapshots(self) -> None:
        """Increment snapshot counter."""
        self.snapshot_count += 1
    
    def increment_motion_events(self) -> None:
        """Increment motion detection counter."""
        self.motion_events += 1
    
    def increment_face_detections(self) -> None:
        """Increment face detection counter."""
        self.face_detections += 1
    
    def increment_qr_detections(self) -> None:
        """Increment QR detection counter."""
        self.qr_detections += 1
    
    def increment_camera_restarts(self) -> None:
        """Increment camera restart counter."""
        self.camera_restarts += 1
    
    def add_recording_duration(self, seconds: float) -> None:
        """Add to recording duration."""
        self.recording_duration += seconds
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get all analytics data."""
        return {
            "metrics": {
                "fps": self.fps_history.get_all(),
                "cpu": self.cpu_history.get_all(),
                "ram": self.ram_history.get_all(),
                "temperature": self.temperature_history.get_all(),
            },
            "stats": {
                "fps_avg": self.fps_history.get_average(),
                "fps_max": self.fps_history.get_max(),
                "fps_min": self.fps_history.get_min(),
                "cpu_avg": self.cpu_history.get_average(),
                "cpu_max": self.cpu_history.get_max(),
                "ram_avg": self.ram_history.get_average(),
                "ram_max": self.ram_history.get_max(),
                "temp_avg": self.temperature_history.get_average(),
                "temp_max": self.temperature_history.get_max(),
            },
            "counters": {
                "snapshots": self.snapshot_count,
                "motion_events": self.motion_events,
                "face_detections": self.face_detections,
                "qr_detections": self.qr_detections,
                "camera_restarts": self.camera_restarts,
                "recording_duration_seconds": self.recording_duration,
            }
        }
    
    def reset(self) -> None:
        """Reset all analytics."""
        self.fps_history.clear()
        self.cpu_history.clear()
        self.ram_history.clear()
        self.temperature_history.clear()
        self.snapshot_count = 0
        self.motion_events = 0
        self.face_detections = 0
        self.qr_detections = 0
        self.camera_restarts = 0
        self.recording_duration = 0.0


# Global instance
analytics_service = AnalyticsService()

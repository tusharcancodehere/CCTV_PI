"""Intelligent adaptive performance engine."""

import time
from enum import Enum
from collections import deque
from datetime import datetime
from services.logger import logger_service
from config.system_config import config

class OptimizationMode(Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTOMATIC = "automatic"

class PerformanceEngine:
    """Monitors performance and dynamically tunes the system."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
            
        self._initialized = True
        self.logger = logger_service.get_logger("perf_engine")
        self.mode = OptimizationMode.AUTOMATIC
        
        self.opt_log = deque(maxlen=50)
        self.advisor_messages = []
        
        # State tracking for hysteresis
        self.last_adjustment_time = time.time()
        self.violation_start = 0.0
        
    def log_optimization(self, parameter: str, old_val, new_val, reason: str):
        """Record an optimization event."""
        event = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "parameter": parameter,
            "change": f"{old_val} → {new_val}",
            "reason": reason
        }
        self.opt_log.append(event)
        self.logger.info(f"Auto-Tuned {parameter}: {old_val} -> {new_val} ({reason})")
        
    def get_optimization_log(self) -> list:
        return list(self.opt_log)
        
    def get_advisor_messages(self) -> list:
        return self.advisor_messages
        
    def evaluate(self, cpu_usage: float, gpu_usage: float, fps: float, target_fps: int):
        """Evaluate system state and apply optimizations."""
        self.advisor_messages = []
        
        # 1. Update Advisor
        if cpu_usage > 90:
            self.advisor_messages.append(f"CPU temperature/load is extremely high ({cpu_usage:.1f}%). System may throttle.")
        elif cpu_usage < 40 and fps >= target_fps - 2:
            self.advisor_messages.append("System healthy. Maintaining target framerate.")
            
        if gpu_usage < 10:
            self.advisor_messages.append(f"GPU utilization is only {gpu_usage:.1f}%. Consider enabling CUDA.")
            
        # 2. Apply Auto-Tuning (if in AUTOMATIC mode)
        if self.mode != OptimizationMode.AUTOMATIC:
            return
            
        now = time.time()
        
        # Hysteresis: wait 5s between changes to prevent oscillation
        if now - self.last_adjustment_time < 5.0:
            return
            
        if cpu_usage > 85.0:
            # We have a violation. Check if sustained for 3 seconds.
            if self.violation_start == 0.0:
                self.violation_start = now
                return
                
            if now - self.violation_start > 3.0:
                # Need to throttle
                from camera.manager import camera_manager
                
                if config.MJPEG_QUALITY > 60:
                    old = config.MJPEG_QUALITY
                    config.MJPEG_QUALITY = max(60, config.MJPEG_QUALITY - 10)
                    self.log_optimization("JPEG Quality", old, config.MJPEG_QUALITY, f"CPU reached {cpu_usage:.1f}%")
                    self.last_adjustment_time = now
                    self.violation_start = 0.0
                    
                elif config.CAMERA_FPS > 15:
                    old = config.CAMERA_FPS
                    # Drop to next tier: 60->45->30->20->15
                    tiers = [15, 20, 30, 45, 60]
                    next_fps = 15
                    for t in reversed(tiers):
                        if t < old:
                            next_fps = t
                            break
                    camera_manager.apply_settings({"fps": next_fps})
                    self.log_optimization("Camera FPS", old, next_fps, "Maintaining stream stability under load")
                    self.last_adjustment_time = now
                    self.violation_start = 0.0
        else:
            self.violation_start = 0.0
            # Try to recover if CPU < 40%
            if cpu_usage < 40.0:
                from camera.manager import camera_manager
                if config.MJPEG_QUALITY < 90:
                    old = config.MJPEG_QUALITY
                    config.MJPEG_QUALITY = min(90, config.MJPEG_QUALITY + 10)
                    self.log_optimization("JPEG Quality", old, config.MJPEG_QUALITY, "CPU load is low, restoring quality")
                    self.last_adjustment_time = now
                    
                elif config.CAMERA_FPS < 30:
                    # Only recover to 30 automatically to avoid pushing hardware too hard natively unless asked
                    old = config.CAMERA_FPS
                    camera_manager.apply_settings({"fps": 30})
                    self.log_optimization("Camera FPS", old, 30, "System load reduced")
                    self.last_adjustment_time = now

performance_engine = PerformanceEngine()

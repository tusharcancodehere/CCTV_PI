"""Performance estimation engine for OpenCV Flask camera settings."""

import platform
from pathlib import Path
from typing import Dict, Any, Tuple
import psutil

from config.system_config import config


class PerformanceEstimator:
    """Estimates CPU, RAM, Latency and Stability ratings for configurations."""

    # Device Profiles
    PROFILES = {
        "Raspberry Pi 4 (1GB)": {
            "cpu_factor": 4.5,
            "ram_base_mb": 180.0,
            "ram_multiplier": 0.20,
            "latency_factor": 3.0,
            "warmup_sec": "3–5 sec",
        },
        "Raspberry Pi 5": {
            "cpu_factor": 2.2,
            "ram_base_mb": 200.0,
            "ram_multiplier": 0.15,
            "latency_factor": 1.5,
            "warmup_sec": "2–3 sec",
        },
        "Low-end laptop": {
            "cpu_factor": 1.0,
            "ram_base_mb": 250.0,
            "ram_multiplier": 0.10,
            "latency_factor": 0.8,
            "warmup_sec": "1–2 sec",
        },
        "High-end laptop": {
            "cpu_factor": 0.3,
            "ram_base_mb": 300.0,
            "ram_multiplier": 0.05,
            "latency_factor": 0.3,
            "warmup_sec": "1 sec",
        }
    }

    # Resolution Modes
    MODES = {
        "LOW": {
            "resolution": (320, 240),
            "description": "Pi-safe mode",
            "recommended_fps": 15,
        },
        "BALANCED": {
            "resolution": (640, 480),
            "description": "default recommended",
            "recommended_fps": 30,
        },
        "HIGH": {
            "resolution": (1280, 720),
            "description": "desktop recommended",
            "recommended_fps": 30,
        },
        "ULTRA": {
            "resolution": (1920, 1080),
            "description": "experimental mode",
            "recommended_fps": 30,
        }
    }

    def auto_detect_device(self) -> str:
        """Detect the hardware type and return a matching profile name."""
        try:
            model_path = Path("/proc/device-tree/model")
            if model_path.exists():
                model = model_path.read_text().lower()
                if "raspberry pi 5" in model:
                    return "Raspberry Pi 5"
                elif "raspberry pi 4" in model:
                    return "Raspberry Pi 4 (1GB)"
                elif "raspberry pi" in model:
                    return "Raspberry Pi 4 (1GB)"
        except Exception:
            pass

        # Check virtual memory to classify laptop types
        try:
            total_ram = psutil.virtual_memory().total / (1024**3)
            # If total RAM < 6GB or CPU is slow, classify as low-end
            if total_ram < 6.0:
                return "Low-end laptop"
        except Exception:
            pass

        return "High-end laptop"

    def get_mode_profile(self, mode: str) -> Dict[str, Any]:
        """Get resolution and info for a named mode."""
        return self.MODES.get(mode.upper(), self.MODES["BALANCED"])

    def predict_latency(self, resolution: Tuple[int, int], encoding_type: str = "jpeg") -> float:
        """Estimate frame processing latency in milliseconds."""
        width, height = resolution
        pixels = width * height
        # Base latency logic: ~6ms for 640x480 on a base 'Low-end laptop' profile
        base_latency = (pixels / 307200) * 6.0
        if encoding_type.lower() == "jpeg":
            base_latency += 2.0  # Add encoding overhead
        return base_latency

    def predict_memory_usage(self, resolution: Tuple[int, int]) -> float:
        """Estimate frame memory footprint in MB."""
        width, height = resolution
        # Base buffer size calculation (BGR frame is width * height * 3 bytes)
        frame_mb = (width * height * 3) / (1024 * 1024)
        # Account for multiple internal pipeline buffers (e.g. current, pre-encoded jpeg, overlays)
        return frame_mb * 5.0

    def predict_cpu_load(self, resolution: Tuple[int, int], fps: int) -> float:
        """Estimate processing CPU utilization percentage."""
        width, height = resolution
        pixels = width * height
        # Base load logic: 640x480 @ 30fps takes ~10% CPU on standard laptop core
        base_load = (pixels / 307200) * (fps / 30) * 10.0
        return base_load

    def estimate(self, resolution: Tuple[int, int], fps: int, device_profile: str) -> Dict[str, Any]:
        """Generate comprehensive performance estimation."""
        profile = self.PROFILES.get(device_profile, self.PROFILES["Low-end laptop"])
        
        # Calculate latency
        latency_factor = profile["latency_factor"]
        latency_ms = self.predict_latency(resolution) * latency_factor
        frame_time_range = f"{int(latency_ms * 0.8)}–{int(latency_ms * 1.2)}ms"
        
        # Calculate CPU Load
        cpu_factor = profile["cpu_factor"]
        cpu_load = self.predict_cpu_load(resolution, fps) * cpu_factor
        cpu_min = min(95.0, max(5.0, cpu_load * 0.8))
        cpu_max = min(100.0, max(10.0, cpu_load * 1.2))
        cpu_range = f"{int(cpu_min)}–{int(cpu_max)}%"
        
        # Calculate RAM Footprint
        ram_base = profile["ram_base_mb"]
        ram_added = self.predict_memory_usage(resolution) * profile["ram_multiplier"] * 10.0
        ram_min = ram_base + (ram_added * 0.8)
        ram_max = ram_base + (ram_added * 1.2)
        ram_range = f"{int(ram_min)}–{int(ram_max)}MB"
        
        # Estimate output FPS (might throttle if CPU is saturated)
        est_fps_max = min(fps, int(1000 / latency_ms))
        if cpu_max > 90.0:
            est_fps_min = max(5, int(est_fps_max * 0.5))
            est_fps_max = max(10, int(est_fps_max * 0.8))
            fps_range = f"{est_fps_min}–{est_fps_max}"
        else:
            fps_range = f"{int(est_fps_max * 0.9)}–{int(est_fps_max)}"
            
        # Determine stability rating (1-5 stars)
        pixels = resolution[0] * resolution[1]
        is_pi = "raspberry" in device_profile.lower()
        
        if pixels >= 1920 * 1080:  # Ultra
            stars = 1 if is_pi else 3
        elif pixels >= 1280 * 720:  # High
            stars = 2 if is_pi else 4
        elif pixels >= 640 * 480:  # Balanced
            stars = 4 if is_pi else 5
        else:  # Low
            stars = 5
            
        # Compile warnings
        warnings = []
        is_pi_warning = False
        
        if is_pi and pixels >= 1280 * 720:
            warnings.append(f"May overheat {device_profile.split(' ')[0]}")
            warnings.append("Not recommended for 1GB models")
            is_pi_warning = True
            
        if cpu_max > 80.0:
            warnings.append(f"Estimated CPU usage is high ({int(cpu_max)}%)")
        if ram_max > 700.0:
            warnings.append("High memory usage may trigger OS OOM killer")
            
        warning_text = "\n".join(warnings) if warnings else None
        
        return {
            "mode": f"{resolution[0]}x{resolution[1]}",
            "fps": fps_range,
            "cpu": cpu_range,
            "ram": ram_range,
            "frame_time": frame_time_range,
            "warmup": profile["warmup_sec"],
            "stability": "★" * stars + "☆" * (5 - stars),
            "stability_stars": stars,
            "warning": warning_text,
            "is_pi_warning": is_pi_warning,
            "device_profile": device_profile
        }

    def auto_suggest(self) -> Dict[str, Any]:
        """Automatically suggest the best mode based on hardware and current load."""
        device = self.auto_detect_device()
        is_pi = "raspberry" in device.lower()
        
        # Get current metrics if available
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        
        if is_pi:
            # Raspberry Pi gets BALANCED by default or LOW if loaded/low-mem
            if ram.total / (1024**3) < 1.5 or cpu_usage > 70.0:
                suggested_mode = "LOW"
            else:
                suggested_mode = "BALANCED"
        else:
            # Laptops get HIGH by default or ULTRA if high-end and not loaded
            if "high-end" in device.lower() and cpu_usage < 50.0:
                suggested_mode = "ULTRA"
            elif cpu_usage > 80.0:
                suggested_mode = "BALANCED"
            else:
                suggested_mode = "HIGH"
                
        profile = self.get_mode_profile(suggested_mode)
        resolution = profile["resolution"]
        recommended_fps = profile["recommended_fps"]
        
        return {
            "device_profile": device,
            "suggested_mode": suggested_mode,
            "resolution": resolution,
            "fps": recommended_fps,
            "estimation": self.estimate(resolution, recommended_fps, device)
        }


# Global instance
performance_estimator = PerformanceEstimator()

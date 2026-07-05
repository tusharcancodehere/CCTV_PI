"""Camera manager - main camera interface."""

import cv2
import threading
import time
from datetime import datetime
from typing import Optional, Tuple
from collections import deque

import numpy as np

from config import config, CameraBackend
from services.logger import logger_service
from services.system_monitor import system_monitor
from camera.stream import StreamGenerator
from camera.detectors import DetectorManager
from camera.controls import CameraControls
from camera.recorder import VideoRecorder
from camera.snapshots import SnapshotCapture


class CameraManager:
    """Manages camera capture and processing."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self.logger = logger_service.get_logger("camera")
        self.camera = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.lifecycle_lock = threading.Lock()
        
        # Components
        self.stream = StreamGenerator(quality=config.MJPEG_QUALITY)
        self.detectors = DetectorManager()
        self.controls = CameraControls()
        self.recorder = VideoRecorder()
        self.snapshots = SnapshotCapture()
        
        # State
        self.should_run = False
        self.connected = False
        self.current_frame: Optional[np.ndarray] = None
        self.fps = 0.0
        self.frame_count = 0
        self.resolution = config.CAMERA_RESOLUTION
        
        # FPS tracking
        self.fps_buffer = deque(maxlen=30)
        self.last_frame_time = time.time()
        self.last_update_time = time.time()
        
        # Resolution info
        self.frame_width = 0
        self.frame_height = 0
    
    def initialize(self) -> bool:
        """Initialize camera."""
        try:
            self.logger.info("Initializing camera...")
            
            # Try Picamera2 first (Raspberry Pi)
            if self._try_picamera2():
                self.logger.info("Using Picamera2 backend")
                self.backend = CameraBackend.PICAMERA2
                return True
            
            # Fallback to OpenCV
            if self._try_opencv():
                self.logger.info("Using OpenCV backend")
                self.backend = CameraBackend.OPENCV
                return True
            
            self.logger.error("No camera backend available")
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def _try_picamera2(self) -> bool:
        """Try to initialize Picamera2."""
        try:
            from picamera2 import Picamera2
            if self.camera:
                try:
                    self.camera.stop()
                except Exception:
                    pass
                self.camera = None
            
            self.camera = Picamera2()
            # Low power / minimum buffer size settings for Pi
            config_dict = self.camera.create_preview_configuration(
                main={"format": "XRGB8888", "size": self.resolution}
            )
            self.camera.configure(config_dict)
            self.camera.start()
            self.frame_width, self.frame_height = self.resolution
            return True
        except ImportError:
            return False
        except Exception as e:
            self.logger.debug(f"Picamera2 failed: {e}")
            return False
    
    def _try_opencv(self) -> bool:
        """Try to initialize OpenCV VideoCapture with fallback."""
        try:
            if self.camera:
                try:
                    self.camera.release()
                except Exception:
                    pass
                self.camera = None
            
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False
            
            # Try configured resolution
            w, h = self.resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            self.camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test frame read
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                self.logger.warning(f"Failed to read test frame at {w}x{h}. Trying 640x480 fallback.")
                w, h = 640, 480
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                ret, test_frame = self.camera.read()
                if not ret or test_frame is None:
                    self.logger.error("Failed to read test frame at fallback resolution.")
                    self.camera.release()
                    self.camera = None
                    return False
            
            self.frame_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (self.frame_width, self.frame_height)
            
            return True
        except Exception as e:
            self.logger.debug(f"OpenCV failed: {e}")
            if self.camera:
                try:
                    self.camera.release()
                except Exception:
                    pass
                self.camera = None
            return False
    
    def start(self) -> bool:
        """Start camera capture thread."""
        with self.lifecycle_lock:
            # Sync settings from store on startup
            try:
                from services.config_service import config_service
                self._apply_settings_under_lock(config_service.get_all_settings())
            except Exception as e:
                self.logger.error(f"Error restoring startup settings: {e}")
            return self._start_under_lock()
    
    def stop(self) -> None:
        """Stop camera capture."""
        with self.lifecycle_lock:
            self._stop_under_lock()
    
    def restart(self) -> bool:
        """Restart camera."""
        with self.lifecycle_lock:
            self._stop_under_lock()
            time.sleep(0.5)
            return self._start_under_lock()
            
    def _start_under_lock(self) -> bool:
        """Start camera capture (must hold lifecycle_lock)."""
        if self.running:
            return True
        
        self.should_run = True
        
        if not self.initialize():
            self.connected = False
            self.running = False
            return False
        
        self.running = True
        self.connected = True
        self.last_update_time = time.time()
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self.capture_thread.start()
        self.logger.info("Camera started")
        return True
        
    def _stop_under_lock(self) -> None:
        """Stop camera capture (must hold lifecycle_lock)."""
        self.should_run = False
        if not self.running:
            return
        
        self.running = False
        
        # Release resource BEFORE joining the thread to unblock the read() call
        if self.camera:
            try:
                if hasattr(self.camera, 'stop'):
                    self.camera.stop()
                elif hasattr(self.camera, 'release'):
                    self.camera.release()
            except Exception as e:
                self.logger.error(f"Error releasing camera: {e}")
        
        self.camera = None
        self.connected = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            self.capture_thread = None
            
        self.logger.info("Camera stopped")
        
    def _recover_camera(self) -> None:
        """Recover camera from a stall."""
        try:
            self.logger.warning("Attempting camera watchdog recovery...")
            self.restart()
            self.logger.info("Camera watchdog recovery complete")
        except Exception as e:
            self.logger.error(f"Camera recovery failed: {e}")
            
    def apply_settings(self, settings: dict) -> bool:
        """Apply camera configuration settings."""
        with self.lifecycle_lock:
            return self._apply_settings_under_lock(settings)

    def _apply_settings_under_lock(self, settings: dict) -> bool:
        """Apply camera settings (must hold lifecycle_lock)."""
        # Toggles
        if "enable_motion_detection" in settings:
            self.detectors.enabled["motion"] = bool(settings["enable_motion_detection"])
        if "enable_face_detection" in settings:
            self.detectors.enabled["face"] = bool(settings["enable_face_detection"])
        if "enable_qr_detection" in settings:
            self.detectors.enabled["qr"] = bool(settings["enable_qr_detection"])
        
        # Controls
        if "brightness" in settings:
            self.controls.set_brightness(int(settings["brightness"]))
        if "contrast" in settings:
            self.controls.set_contrast(float(settings["contrast"]))
        if "saturation" in settings:
            self.controls.set_saturation(float(settings["saturation"]))
        if "flip_horizontal" in settings or "flip_vertical" in settings:
            h = settings.get("flip_horizontal", self.controls.flip_h)
            v = settings.get("flip_vertical", self.controls.flip_v)
            self.controls.set_flip(bool(h), bool(v))
        if "rotate" in settings:
            self.controls.set_rotate(int(settings["rotate"]))
            
        # Reconfigure resolution/fps
        restart_needed = False
        if "resolution" in settings:
            new_res = tuple(settings["resolution"])
            if new_res != self.resolution:
                self.resolution = new_res
                restart_needed = True
        if "fps" in settings:
            new_fps = int(settings["fps"])
            from config import config
            if new_fps != config.CAMERA_FPS:
                config.CAMERA_FPS = new_fps
                restart_needed = True
                
        if restart_needed and self.running:
            self.logger.info("Settings change requires camera restart. Restarting...")
            self._stop_under_lock()
            time.sleep(0.5)
            return self._start_under_lock()
            
        return True
    
    def _capture_loop(self) -> None:
        """Main capture loop with adaptive throttling."""
        self.last_update_time = time.time()
        
        while self.running:
            try:
                frame = self._read_frame()
                
                if frame is None:
                    self.connected = False
                    time.sleep(0.1)
                    continue
                
                self.connected = True
                self.frame_count += 1
                
                # Check CPU load from analytics history (updated at 1Hz)
                from services.analytics import analytics_service
                cpu_usage = analytics_service.cpu_history.get_average() if hasattr(analytics_service, 'cpu_history') else 0.0
                
                # Adaptive frame skip based on CPU load
                skip_processing = False
                if cpu_usage > 90.0:
                    skip_processing = (self.frame_count % 5 != 0)  # ~6 FPS
                elif cpu_usage > 75.0:
                    skip_processing = (self.frame_count % 3 != 0)  # ~10 FPS
                elif cpu_usage > 60.0:
                    skip_processing = (self.frame_count % 2 != 0)  # ~15 FPS
                
                if skip_processing:
                    time.sleep(0.001)
                    continue
                
                self._update_fps()
                
                # Adaptive detector throttling
                run_detection = True
                if cpu_usage > 50.0:
                    run_detection = (self.frame_count % 2 == 0)
                
                if run_detection:
                    detections = self.detectors.detect_all(frame)
                else:
                    detections = {"motion": None, "faces": [], "qr_codes": []}
                
                # Update analytics counters
                if detections.get("motion") and detections["motion"].get("detected"):
                    analytics_service.increment_motion_events()
                if detections.get("faces"):
                    analytics_service.increment_face_detections()
                if detections.get("qr_codes"):
                    analytics_service.increment_qr_detections()
                
                # Apply camera control adjustments
                frame = self.controls.apply_all(frame)
                
                # Update MJPEG stream pre-encoded JPEG and annotations
                self.stream.set_detections(
                    detections.get("faces", []),
                    detections.get("motion")
                )
                self.stream.update_frame(frame, self.fps)
                
                # Write to recording
                if self.recorder.is_recording():
                    self.recorder.write_frame(frame)
                
                # Store current frame
                with self.lock:
                    self.current_frame = frame
                    self.last_update_time = time.time()
                
                system_monitor.update_frame_count(self.frame_count)
                system_monitor.update_fps(self.fps)
            
            except Exception as e:
                self.logger.error(f"Capture loop error: {e}")
                time.sleep(0.1)
    
    def _read_frame(self) -> Optional[np.ndarray]:
        """Read single frame from camera."""
        if not self.camera:
            return None
        
        try:
            if hasattr(self.camera, 'capture_array'):
                # Picamera2
                frame = self.camera.capture_array()
                if frame is None:
                    return None
                # Convert XRGB to BGR
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                # OpenCV
                ret, frame = self.camera.read()
                return frame if ret else None
        
        except Exception as e:
            self.logger.error(f"Frame read error: {e}")
            return None
    
    def _update_fps(self) -> None:
        """Update FPS calculation."""
        current_time = time.time()
        delta = current_time - self.last_frame_time
        
        if delta > 0:
            fps = 1.0 / delta
            self.fps_buffer.append(fps)
            self.fps = sum(self.fps_buffer) / len(self.fps_buffer)
        
        self.last_frame_time = current_time
    
    def capture_snapshot(self) -> Optional[str]:
        """Capture a snapshot."""
        with self.lock:
            frame = self.current_frame
            if frame is not None:
                # Copy buffer for file writing to avoid capture loop race
                frame = frame.copy()
        
        if frame is None:
            return None
        
        path = self.snapshots.capture(frame)
        return str(path) if path else None
    
    def start_recording(self) -> bool:
        """Start video recording."""
        started = self.recorder.start_recording(self.resolution)
        self.stream.set_recording(True)
        system_monitor.set_recording(True)
        return started
    
    def stop_recording(self) -> dict:
        """Stop video recording."""
        result = self.recorder.stop_recording()
        self.stream.set_recording(False)
        system_monitor.set_recording(False)
        return result
    
    def is_recording(self) -> bool:
        """Check if recording."""
        return self.recorder.is_recording()
    
    def get_status(self) -> dict:
        """Get camera status."""
        return {
            "connected": self.connected,
            "running": self.running,
            "fps": round(self.fps, 2),
            "resolution": self.resolution,
            "frame_count": self.frame_count,
            "recording": self.is_recording(),
            "backend": self.backend.value if hasattr(self, 'backend') else "unknown"
        }
    
    def get_stream_generator(self):
        """Get MJPEG stream generator."""
        return self.stream.generate()
    
    def get_current_frame_jpeg(self) -> Optional[bytes]:
        """Get current frame as JPEG."""
        return self.stream.get_jpeg()
    
    def set_brightness(self, value: int) -> None:
        """Set brightness."""
        self.controls.set_brightness(value)
    
    def set_contrast(self, value: float) -> None:
        """Set contrast."""
        self.controls.set_contrast(value)
    
    def set_saturation(self, value: float) -> None:
        """Set saturation."""
        self.controls.set_saturation(value)
    
    def set_flip(self, horizontal: bool, vertical: bool) -> None:
        """Set flip settings."""
        self.controls.set_flip(horizontal, vertical)
    
    def set_rotate(self, angle: int) -> None:
        """Set rotation."""
        self.controls.set_rotate(angle)


# Global instance
camera_manager = CameraManager()

"""Camera manager - advanced multi-threaded asynchronous pipeline."""

import cv2
import threading
import time
import queue
from datetime import datetime
from typing import Optional, Tuple
from collections import deque

import numpy as np

from config.system_config import config, CameraBackend
from services.logger import logger_service
from services.system_monitor import system_monitor
from services.analytics import analytics_service
from services.gpu_manager import gpu_manager
from camera.stream import StreamGenerator
from camera.detectors import DetectorManager
from camera.controls import CameraControls
from camera.recorder import VideoRecorder
from camera.snapshots import SnapshotCapture


class CameraManager:
    """Manages multi-threaded asynchronous camera pipeline."""
    
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
        
        # Threads
        self.capture_thread: Optional[threading.Thread] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.encoding_thread: Optional[threading.Thread] = None
        
        # Synchronization
        self.lock = threading.Lock()
        self.lifecycle_lock = threading.Lock()
        
        # Queues (Producer-Consumer)
        self.raw_queue = queue.Queue(maxsize=config.CAMERA_BUFFER_SIZE)
        self.encode_queue = queue.Queue(maxsize=config.MJPEG_BUFFER_SIZE)
        
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
        self.dropped_frames = 0
        self.queue_wait_time = 0.0
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
            
            if self._try_picamera2():
                self.logger.info("Using Picamera2 backend")
                self.backend = CameraBackend.PICAMERA2
                return True
            
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
        try:
            from picamera2 import Picamera2
            if self.camera:
                try: self.camera.stop()
                except Exception: pass
                self.camera = None
            
            self.camera = Picamera2()
            config_dict = self.camera.create_preview_configuration(
                main={"format": "XRGB8888", "size": self.resolution}
            )
            self.camera.configure(config_dict)
            self.camera.start()
            self.frame_width, self.frame_height = self.resolution
            return True
        except Exception:
            return False
    
    def _try_opencv(self) -> bool:
        try:
            if self.camera:
                try: self.camera.release()
                except Exception: pass
                self.camera = None
            
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False
            
            w, h = self.resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            self.camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                self.logger.warning(f"Failed to read test frame at {w}x{h}. Trying 640x480 fallback.")
                w, h = 640, 480
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                ret, test_frame = self.camera.read()
                if not ret or test_frame is None:
                    self.camera.release()
                    self.camera = None
                    return False
            
            self.frame_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (self.frame_width, self.frame_height)
            return True
        except Exception as e:
            self.logger.debug(f"OpenCV failed: {e}")
            return False
    
    def start(self) -> bool:
        with self.lifecycle_lock:
            try:
                from services.config_service import config_service
                self._apply_settings_under_lock(config_service.get_all_settings())
            except Exception as e:
                self.logger.error(f"Error restoring startup settings: {e}")
            return self._start_under_lock()
    
    def stop(self) -> None:
        with self.lifecycle_lock:
            self._stop_under_lock()
    
    def restart(self) -> bool:
        with self.lifecycle_lock:
            self._stop_under_lock()
            time.sleep(0.5)
            return self._start_under_lock()
            
    def _start_under_lock(self) -> bool:
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
        
        # Flush queues
        while not self.raw_queue.empty():
            try: self.raw_queue.get_nowait()
            except queue.Empty: break
        while not self.encode_queue.empty():
            try: self.encode_queue.get_nowait()
            except queue.Empty: break
            
        self.dropped_frames = 0
            
        self.capture_thread = threading.Thread(target=self._capture_thread_func, daemon=True, name="CaptureThread")
        self.processing_thread = threading.Thread(target=self._processing_thread_func, daemon=True, name="ProcessThread")
        self.encoding_thread = threading.Thread(target=self._encoding_thread_func, daemon=True, name="EncodeThread")
        
        self.capture_thread.start()
        self.processing_thread.start()
        self.encoding_thread.start()
        
        self.logger.info("Camera asynchronous pipeline started")
        return True
        
    def _stop_under_lock(self) -> None:
        self.should_run = False
        if not self.running:
            return
        
        self.running = False
        
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
        
        # Send poison pills
        try: self.raw_queue.put(None, timeout=1)
        except queue.Full: pass
        try: self.encode_queue.put(None, timeout=1)
        except queue.Full: pass
        
        if self.capture_thread: self.capture_thread.join(timeout=1.0)
        if self.processing_thread: self.processing_thread.join(timeout=1.0)
        if self.encoding_thread: self.encoding_thread.join(timeout=1.0)
            
        self.logger.info("Camera asynchronous pipeline stopped")
        
    def _recover_camera(self) -> None:
        try:
            self.logger.warning("Attempting camera watchdog recovery...")
            self.restart()
        except Exception as e:
            self.logger.error(f"Camera recovery failed: {e}")
            
    def apply_settings(self, settings: dict) -> bool:
        with self.lifecycle_lock:
            return self._apply_settings_under_lock(settings)

    def _apply_settings_under_lock(self, settings: dict) -> bool:
        if "enable_motion_detection" in settings:
            self.detectors.enabled["motion"] = bool(settings["enable_motion_detection"])
        if "enable_face_detection" in settings:
            self.detectors.enabled["face"] = bool(settings["enable_face_detection"])
        if "enable_qr_detection" in settings:
            self.detectors.enabled["qr"] = bool(settings["enable_qr_detection"])
        
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
            
        if "mirror_preview" in settings:
            self.stream.mirror_preview = bool(settings["mirror_preview"])
            
        restart_needed = False
        if "resolution" in settings:
            new_res = tuple(settings["resolution"])
            if new_res != self.resolution:
                self.resolution = new_res
                restart_needed = True
        if "fps" in settings:
            new_fps = int(settings["fps"])
            from config.system_config import config
            if new_fps != config.CAMERA_FPS:
                config.CAMERA_FPS = new_fps
                restart_needed = True
                
        if restart_needed and self.running:
            self.logger.info("Settings change requires camera restart. Restarting...")
            self.detectors.reset()
            self._stop_under_lock()
            time.sleep(0.5)
            return self._start_under_lock()
            
        return True
    
    # --- PIPELINE THREADS ---
    
    def _capture_thread_func(self) -> None:
        """Stage 1: Hardware capture."""
        while self.running:
            try:
                t_read_start = time.perf_counter()
                frame = self._read_frame()
                
                if frame is None:
                    self.connected = False
                    time.sleep(0.1)
                    continue
                
                self.connected = True
                
                try:
                    self.raw_queue.put_nowait((frame, t_read_start))
                except queue.Full:
                    self.dropped_frames += 1
                    
            except Exception as e:
                self.logger.error(f"Capture error: {e}")
                time.sleep(0.1)

    def _processing_thread_func(self) -> None:
        """Stage 2: OpenCV operations (GPU accelerated)."""
        while self.running:
            try:
                payload = self.raw_queue.get(timeout=0.5)
                if payload is None:
                    break
                
                frame, t_read_start = payload
                q_wait_start = time.perf_counter()
                
                # Check CPU load from analytics history
                cpu_usage = analytics_service.cpu_history.get_average() if hasattr(analytics_service, 'cpu_history') else 0.0
                
                # Adaptive detector throttling
                run_detection = True
                if cpu_usage > 70.0:
                    run_detection = (self.frame_count % 3 == 0)
                elif cpu_usage > 50.0:
                    run_detection = (self.frame_count % 2 == 0)
                
                t_detect_start = time.perf_counter()
                if run_detection:
                    detections = self.detectors.detect_all(frame)
                else:
                    detections = {"motion": None, "faces": [], "qr_codes": []}
                t_detect_end = time.perf_counter()
                detector_ms = (t_detect_end - t_detect_start) * 1000.0
                
                if detections.get("motion") and detections["motion"].get("detected"):
                    analytics_service.increment_motion_events()
                if detections.get("faces"):
                    analytics_service.increment_face_detections()
                if detections.get("qr_codes"):
                    analytics_service.increment_qr_detections()
                
                t_process_start = time.perf_counter()
                # Apply controls (which uses gpu_manager internally via controls or directly here)
                frame = self.controls.apply_all(frame)
                t_process_end = time.perf_counter()
                process_ms = (t_process_end - t_process_start) * 1000.0
                
                q_wait_time = (time.perf_counter() - q_wait_start) * 1000.0
                self.queue_wait_time = (self.queue_wait_time * 0.9) + (q_wait_time * 0.1)
                
                try:
                    self.encode_queue.put_nowait((frame, detections, t_read_start, detector_ms, process_ms))
                except queue.Full:
                    self.dropped_frames += 1
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Processing error: {e}")

    def _encoding_thread_func(self) -> None:
        """Stage 3: JPEG Encoding and Stream Delivery."""
        while self.running:
            try:
                payload = self.encode_queue.get(timeout=0.5)
                if payload is None:
                    break
                
                frame, detections, t_read_start, detector_ms, process_ms = payload
                
                self.frame_count += 1
                self._update_fps()
                
                # Write to recording
                if self.recorder.is_recording():
                    self.recorder.write_frame(frame)
                
                t_encode_start = time.perf_counter()
                self.stream.set_detections(detections.get("faces", []), detections.get("motion"))
                self.stream.update_frame(frame, self.fps)
                t_encode_end = time.perf_counter()
                encode_ms = (t_encode_end - t_encode_start) * 1000.0
                
                total_latency = (time.perf_counter() - t_read_start) * 1000.0
                
                with self.lock:
                    self.current_frame = frame
                    self.last_update_time = time.time()
                
                analytics_service.record_timing(
                    latency=total_latency,
                    processing=process_ms,
                    detector=detector_ms,
                    encoding=encode_ms
                )
                
                system_monitor.update_frame_count(self.frame_count)
                system_monitor.update_fps(self.fps)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Encoding error: {e}")

    # --- HELPERS ---
    
    def _read_frame(self) -> Optional[np.ndarray]:
        if not self.camera: return None
        try:
            if hasattr(self.camera, 'capture_array'):
                frame = self.camera.capture_array()
                if frame is None: return None
                return gpu_manager.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = self.camera.read()
                return frame if ret else None
        except Exception:
            return None
    
    def _update_fps(self) -> None:
        current_time = time.time()
        delta = current_time - self.last_frame_time
        if delta > 0:
            fps = 1.0 / delta
            self.fps_buffer.append(fps)
            self.fps = sum(self.fps_buffer) / len(self.fps_buffer)
        self.last_frame_time = current_time
    
    def capture_snapshot(self) -> Optional[str]:
        with self.lock:
            frame = self.current_frame
            if frame is not None: frame = frame.copy()
        if frame is None: return None
        path = self.snapshots.capture(frame)
        return str(path) if path else None
    
    def start_recording(self) -> bool:
        started = self.recorder.start_recording(self.resolution)
        self.stream.set_recording(True)
        system_monitor.set_recording(True)
        return started
    
    def stop_recording(self) -> dict:
        result = self.recorder.stop_recording()
        self.stream.set_recording(False)
        system_monitor.set_recording(False)
        return result
    
    def is_recording(self) -> bool:
        return self.recorder.is_recording()
    
    def get_status(self) -> dict:
        return {
            "connected": self.connected,
            "running": self.running,
            "fps": round(self.fps, 2),
            "resolution": self.resolution,
            "frame_count": self.frame_count,
            "dropped_frames": self.dropped_frames,
            "raw_queue_size": self.raw_queue.qsize(),
            "encode_queue_size": self.encode_queue.qsize(),
            "queue_wait_ms": round(self.queue_wait_time, 2),
            "recording": self.is_recording(),
            "backend": self.backend.value if hasattr(self, 'backend') else "unknown"
        }
    
    def get_stream_generator(self):
        return self.stream.generate()
    
    def get_current_frame_jpeg(self) -> Optional[bytes]:
        return self.stream.get_jpeg()
    
    def set_brightness(self, value: int) -> None:
        self.controls.set_brightness(value)
    
    def set_contrast(self, value: float) -> None:
        self.controls.set_contrast(value)
    
    def set_saturation(self, value: float) -> None:
        self.controls.set_saturation(value)
    
    def set_flip(self, horizontal: bool, vertical: bool) -> None:
        self.controls.set_flip(horizontal, vertical)
    
    def set_rotate(self, angle: int) -> None:
        self.controls.set_rotate(angle)


# Global instance
camera_manager = CameraManager()

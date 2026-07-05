"""MJPEG streaming thread handler."""

import cv2
import threading
from datetime import datetime
from typing import Optional, Generator
import time

import numpy as np

from config.system_config import config
from camera.overlays import HUDRenderer


def get_fallback_jpeg() -> bytes:
    """Generate a fallback JPEG image indicating camera is offline."""
    img = np.zeros((480, 640, 3), dtype=np.uint8) + 50  # dark grey
    text = "CAMERA OFFLINE"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    color = (0, 0, 255)  # Red
    thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    text_y = (img.shape[0] + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)
    
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, ts, (10, img.shape[0] - 10), font, 0.5, (200, 200, 200), 1)
    
    ret, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes() if ret else b""


class StreamGenerator:
    """Generates MJPEG stream from frames."""
    
    def __init__(self, quality: int = 80):
        self.quality = quality
        self.current_frame = None
        self.current_jpeg: Optional[bytes] = None
        self.frame_id = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.hud = HUDRenderer()
        self.fps = 30
        self.resolution = config.CAMERA_RESOLUTION
        self.recording = False
        self.face_detections = []
        self.motion_data = None
        self.mirror_preview = config.MIRROR_PREVIEW
    
    def update_frame(self, frame: np.ndarray, fps: float = 30) -> None:
        """Update the current frame to be streamed."""
        if frame is None:
            return
        
        with self.lock:
            # Apply display mirror if enabled (doesn't modify original frame reference for recordings)
            if self.mirror_preview:
                frame = cv2.flip(frame, 1)
            
            # Add HUD overlay in-place (no numpy copy to save RAM/CPU)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.hud.render_hud(
                frame, fps,
                self.resolution,
                timestamp,
                self.recording,
                self.face_detections,
                self.motion_data,
                show_grid=False
            )
            
            self.current_frame = frame
            self.fps = fps
            
            # Pre-encode exactly once per frame (shared by all streaming clients)
            ret, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            )
            if ret:
                self.current_jpeg = buffer.tobytes()
                self.frame_id += 1
                self.condition.notify_all()
    
    def set_recording(self, status: bool) -> None:
        """Update recording status indicator."""
        self.recording = status
    
    def set_detections(self, faces: list, motion: dict) -> None:
        """Update detection data."""
        self.face_detections = faces
        self.motion_data = motion
    
    def generate(self) -> Generator[bytes, None, None]:
        """Generate MJPEG stream using thread condition variables (0% idle CPU)."""
        last_yielded_id = -1
        
        while True:
            frame_bytes = None
            with self.lock:
                # Wait for a new frame, timeout to check server/client connection health
                has_new = self.condition.wait_for(
                    lambda: self.frame_id > last_yielded_id,
                    timeout=1.0
                )
                if has_new:
                    frame_bytes = self.current_jpeg
                    last_yielded_id = self.frame_id
            
            # If no frame is available or camera is disconnected, yield fallback frame
            if frame_bytes is None:
                from camera import camera_manager
                if not camera_manager.connected:
                    frame_bytes = get_fallback_jpeg()
                else:
                    continue
            
            try:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
                    + frame_bytes + b"\r\n"
                )
                
                # Sleep if yielding fallback to throttle frame rate
                from camera import camera_manager
                if not camera_manager.connected:
                    time.sleep(1.0)
            except (ConnectionResetError, BrokenPipeError, GeneratorExit):
                # Clean exit on client disconnection (no zombie threads)
                break
    
    def get_jpeg(self) -> Optional[bytes]:
        """Get current frame as JPEG bytes immediately."""
        with self.lock:
            return self.current_jpeg

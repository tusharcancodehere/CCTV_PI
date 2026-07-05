"""Video recording functionality."""

import cv2
import threading
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

import numpy as np

from config import config
from services.storage import storage_service
from services.logger import logger_service


class VideoRecorder:
    """Records video frames to MP4."""
    
    def __init__(self):
        self.recording = False
        self.writer: Optional[cv2.VideoWriter] = None
        self.output_file: Optional[Path] = None
        self.lock = threading.Lock()
        self.logger = logger_service.get_logger("recorder")
        self.frame_count = 0
        self.start_time: Optional[datetime] = None
        self.resolution: Optional[tuple] = None
    
    def start_recording(self, resolution: tuple = None) -> bool:
        """Start video recording."""
        if self.recording:
            return False
        
        try:
            with self.lock:
                if resolution is None:
                    resolution = config.CAMERA_RESOLUTION
                
                self.resolution = resolution
                self.output_file = config.RECORDINGS_DIR / storage_service.get_recording_filename()
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = config.CAMERA_FPS
                
                self.writer = cv2.VideoWriter(
                    str(self.output_file),
                    fourcc,
                    fps,
                    resolution
                )
                
                if not self.writer.isOpened():
                    self.logger.error("Failed to create video writer")
                    self.writer = None
                    self.resolution = None
                    return False
                
                self.recording = True
                self.frame_count = 0
                self.start_time = datetime.now()
                self.logger.info(f"Recording started: {self.output_file.name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def write_frame(self, frame: np.ndarray) -> bool:
        """Write frame to recording."""
        if not self.recording or self.writer is None or frame is None:
            return False
        
        try:
            with self.lock:
                h, w = frame.shape[:2]
                if (w, h) != self.resolution:
                    # Resize if needed
                    frame = cv2.resize(frame, self.resolution)
                
                self.writer.write(frame)
                self.frame_count += 1
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to write frame: {e}")
            return False
    
    def stop_recording(self) -> dict:
        """Stop recording and return metadata."""
        if not self.recording or self.writer is None:
            return {}
        
        try:
            with self.lock:
                self.writer.release()
                self.writer = None
                self.resolution = None
                self.recording = False
                
                duration = (datetime.now() - self.start_time).total_seconds()
                
                result = {
                    "filename": self.output_file.name,
                    "path": str(self.output_file),
                    "duration_seconds": duration,
                    "frame_count": self.frame_count,
                    "size_mb": self.output_file.stat().st_size / (1024 * 1024)
                }
                
                self.logger.info(
                    f"Recording stopped: {self.output_file.name} "
                    f"({duration:.1f}s, {self.frame_count} frames)"
                )
                
                return result
        
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return {}
    
    def is_recording(self) -> bool:
        """Check if recording is active."""
        with self.lock:
            return self.recording
    
    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        if not self.recording or self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

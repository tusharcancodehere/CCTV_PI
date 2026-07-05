"""HUD overlay rendering for camera stream."""

import cv2
import numpy as np
from typing import Tuple, Optional


class HUDRenderer:
    """Renders HUD overlay on frames."""
    
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
        self.text_color = (0, 245, 212)  # Cyan
        self.border_color = (43, 52, 64)  # Dark
    
    def render_fps(self, frame: np.ndarray, fps: float) -> np.ndarray:
        """Render FPS counter."""
        text = f"FPS: {fps:.1f}"
        cv2.putText(frame, text, (10, 30),
                   self.font, self.font_scale,
                   self.text_color, self.font_thickness)
        return frame
    
    def render_resolution(self, frame: np.ndarray, 
                         width: int, height: int) -> np.ndarray:
        """Render resolution."""
        text = f"{width}x{height}"
        cv2.putText(frame, text, (10, 55),
                   self.font, self.font_scale,
                   self.text_color, self.font_thickness)
        return frame
    
    def render_timestamp(self, frame: np.ndarray, 
                        timestamp: str) -> np.ndarray:
        """Render timestamp."""
        height = frame.shape[0]
        cv2.putText(frame, timestamp, (10, height - 20),
                   self.font, self.font_scale,
                   self.text_color, self.font_thickness)
        return frame
    
    def render_recording_indicator(self, frame: np.ndarray) -> np.ndarray:
        """Render recording indicator (red dot)."""
        cv2.circle(frame, (30, 30), 5, (0, 0, 255), -1)
        return frame
    
    def render_face_boxes(self, frame: np.ndarray, 
                         faces: list) -> np.ndarray:
        """Draw bounding boxes around detected faces."""
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h),
                         (0, 255, 0), 2)
        return frame
    
    def render_motion_indicator(self, frame: np.ndarray, 
                               motion_detected: bool) -> np.ndarray:
        """Render motion detection indicator."""
        if motion_detected:
            cv2.rectangle(frame, (5, 5), (50, 50),
                         (0, 165, 255), 2)
        return frame
    
    def render_grid(self, frame: np.ndarray, 
                    grid_size: int = 50) -> np.ndarray:
        """Render subtle grid overlay."""
        height, width = frame.shape[:2]
        
        # Draw grid lines with very low opacity
        overlay = frame.copy()
        alpha = 0.1
        
        for x in range(0, width, grid_size):
            cv2.line(overlay, (x, 0), (x, height),
                    (43, 52, 64), 1)
        
        for y in range(0, height, grid_size):
            cv2.line(overlay, (0, y), (width, y),
                    (43, 52, 64), 1)
        
        frame = cv2.addWeighted(frame, 1 - alpha,
                               overlay, alpha, 0)
        return frame
    
    def render_hud(self, frame: np.ndarray, 
                   fps: float, resolution: Tuple[int, int],
                   timestamp: str, recording: bool = False,
                   faces: list = None, motion: dict = None,
                   show_grid: bool = False) -> np.ndarray:
        """Render complete HUD."""
        if show_grid:
            frame = self.render_grid(frame)
        
        frame = self.render_fps(frame, fps)
        frame = self.render_resolution(frame, resolution[0], resolution[1])
        frame = self.render_timestamp(frame, timestamp)
        
        if recording:
            frame = self.render_recording_indicator(frame)
        
        if faces:
            frame = self.render_face_boxes(frame, faces)
        
        if motion and motion.get("detected"):
            frame = self.render_motion_indicator(frame, True)
        
        return frame

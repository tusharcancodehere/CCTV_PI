"""Camera control utilities."""

import cv2
import numpy as np
from typing import Optional


class CameraControls:
    """Handles camera parameter adjustments."""
    
    def __init__(self):
        self.brightness = 0
        self.contrast = 1.0
        self.saturation = 1.0
        self.hue = 0
        self.flip_h = False
        self.flip_v = False
        self.rotate = 0  # 0, 90, 180, 270
    
    def apply_brightness(self, frame: np.ndarray, 
                        value: int) -> np.ndarray:
        """Adjust brightness."""
        value = max(-100, min(100, value))
        if value == 0:
            return frame
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * (1 + value / 100.0)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def apply_contrast(self, frame: np.ndarray, 
                      value: float) -> np.ndarray:
        """Adjust contrast."""
        value = max(0.5, min(3.0, value))
        if value == 1.0:
            return frame
        
        return cv2.convertScaleAbs(frame, alpha=value, beta=0)
    
    def apply_saturation(self, frame: np.ndarray, 
                        value: float) -> np.ndarray:
        """Adjust saturation."""
        value = max(0.0, min(2.0, value))
        if value == 1.0:
            return frame
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = hsv[:, :, 1] * value
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def apply_flip(self, frame: np.ndarray, 
                   horizontal: bool = False,
                   vertical: bool = False) -> np.ndarray:
        """Apply flip transformations."""
        if horizontal and vertical:
            return cv2.flip(frame, -1)
        elif horizontal:
            return cv2.flip(frame, 1)
        elif vertical:
            return cv2.flip(frame, 0)
        return frame
    
    def apply_rotate(self, frame: np.ndarray, 
                    angle: int) -> np.ndarray:
        """Rotate frame (0, 90, 180, 270)."""
        angle = angle % 360
        if angle == 0:
            return frame
        elif angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def apply_all(self, frame: np.ndarray) -> np.ndarray:
        """Apply all active transformations."""
        frame = self.apply_brightness(frame, self.brightness)
        frame = self.apply_contrast(frame, self.contrast)
        frame = self.apply_saturation(frame, self.saturation)
        frame = self.apply_flip(frame, self.flip_h, self.flip_v)
        frame = self.apply_rotate(frame, self.rotate)
        return frame
    
    def set_brightness(self, value: int) -> None:
        """Set brightness value."""
        self.brightness = max(-100, min(100, value))
    
    def set_contrast(self, value: float) -> None:
        """Set contrast value."""
        self.contrast = max(0.5, min(3.0, value))
    
    def set_saturation(self, value: float) -> None:
        """Set saturation value."""
        self.saturation = max(0.0, min(2.0, value))
    
    def set_flip(self, horizontal: bool, vertical: bool) -> None:
        """Set flip settings."""
        self.flip_h = horizontal
        self.flip_v = vertical
    
    def set_rotate(self, angle: int) -> None:
        """Set rotation angle."""
        self.rotate = angle % 360
    
    def reset(self) -> None:
        """Reset all controls to defaults."""
        self.brightness = 0
        self.contrast = 1.0
        self.saturation = 1.0
        self.hue = 0
        self.flip_h = False
        self.flip_v = False
        self.rotate = 0

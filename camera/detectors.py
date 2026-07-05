"""Camera frame detection modules."""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class Detection:
    """Represents a detection result."""
    type: str  # "motion", "face", "qr"
    confidence: float
    data: dict


class MotionDetector:
    """Lightweight motion detection using frame differencing."""
    
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self.prev_frame = None
        self.motion_detected = False
    
    def detect(self, frame: np.ndarray) -> Tuple[bool, float]:
        """Detect motion in frame."""
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return False, 0.0
        
        current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Frame differencing
        diff = cv2.absdiff(self.prev_frame, current)
        _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
        
        # Calculate motion percentage
        motion_percent = np.sum(thresh) / (thresh.size * 255) * 100
        
        self.prev_frame = current
        self.motion_detected = motion_percent > 1.0
        
        return self.motion_detected, motion_percent
    
    def reset(self) -> None:
        """Reset motion detector."""
        self.prev_frame = None
        self.motion_detected = False


class FaceDetector:
    """Face detection using Haar Cascade (lightweight)."""
    
    def __init__(self):
        self.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.faces = []
    
    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return self.faces.tolist() if len(self.faces) > 0 else []


class QRDetector:
    """QR code detection using OpenCV."""
    
    def __init__(self):
        try:
            self.detector = cv2.QRCodeDetector()
        except AttributeError:
            self.detector = None
        self.qr_data = []
    
    def detect(self, frame: np.ndarray) -> List[dict]:
        """Detect QR codes in frame."""
        if self.detector is None:
            return []
        
        try:
            ret, decoded_info, points, straight_qr = self.detector.detectAndDecodeMulti(frame)
            if ret:
                self.qr_data = [
                    {"data": data, "points": pts}
                    for data, pts in zip(decoded_info, points)
                ]
            else:
                self.qr_data = []
        except Exception:
            self.qr_data = []
        
        return self.qr_data


class DetectorManager:
    """Manages all detectors."""
    
    def __init__(self):
        self.motion = MotionDetector()
        self.face = FaceDetector()
        self.qr = QRDetector()
        self.enabled = {
            "motion": True,
            "face": True,
            "qr": True,
        }
    
    def enable(self, detector_name: str) -> None:
        """Enable a detector."""
        if detector_name in self.enabled:
            self.enabled[detector_name] = True
    
    def disable(self, detector_name: str) -> None:
        """Disable a detector."""
        if detector_name in self.enabled:
            self.enabled[detector_name] = False
    
    def detect_all(self, frame: np.ndarray) -> dict:
        """Run all enabled detectors with frame downscaling."""
        results = {
            "motion": None,
            "faces": [],
            "qr_codes": []
        }
        
        # Downscale frame for detection to save CPU/RAM
        h, w = frame.shape[:2]
        target_w = config.FRAME_RESIZE_WIDTH
        
        if w > target_w:
            scale = target_w / w
            target_h = int(h * scale)
            # INTER_NEAREST is the fastest interpolation
            resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
        else:
            scale = 1.0
            resized = frame
        
        if self.enabled.get("motion", False):
            detected, confidence = self.motion.detect(resized)
            results["motion"] = {"detected": detected, "confidence": confidence}
        
        if self.enabled.get("face", False):
            faces = self.face.detect(resized)
            # Scale coordinates back up
            if scale != 1.0 and faces:
                inv_scale = 1.0 / scale
                faces = [
                    [int(coord * inv_scale) for coord in face]
                    for face in faces
                ]
            results["faces"] = faces
        
        if self.enabled.get("qr", False):
            qr_codes = self.qr.detect(resized)
            # Scale points back up
            if scale != 1.0 and qr_codes:
                inv_scale = 1.0 / scale
                for qr in qr_codes:
                    if "points" in qr and qr["points"] is not None:
                        qr["points"] = qr["points"] * inv_scale
            results["qr_codes"] = qr_codes
        
        return results
    
    def reset(self) -> None:
        """Reset all detectors."""
        self.motion.reset()

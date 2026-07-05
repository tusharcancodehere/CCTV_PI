"""Snapshot capture functionality."""

import cv2
from datetime import datetime
from typing import Optional
from pathlib import Path

import numpy as np

from config.system_config import config
from services.storage import storage_service
from services.logger import logger_service


class SnapshotCapture:
    """Captures and saves snapshots."""
    
    def __init__(self):
        self.logger = logger_service.get_logger("snapshots")
        self.last_snapshot: Optional[Path] = None
    
    def capture(self, frame: np.ndarray) -> Optional[Path]:
        """Capture and save a snapshot."""
        if frame is None:
            self.logger.warning("Cannot capture: frame is None")
            return None
        
        try:
            filename = storage_service.get_snapshot_filename()
            filepath = config.SNAPSHOTS_DIR / filename
            
            success = cv2.imwrite(str(filepath), frame)
            
            if success:
                self.last_snapshot = filepath
                file_size = filepath.stat().st_size / 1024
                self.logger.info(f"Snapshot saved: {filename} ({file_size:.1f} KB)")
                return filepath
            else:
                self.logger.error(f"Failed to save snapshot: {filename}")
                return None
        
        except Exception as e:
            self.logger.error(f"Exception during snapshot capture: {e}")
            return None
    
    def get_last_snapshot(self) -> Optional[Path]:
        """Get path to last captured snapshot."""
        return self.last_snapshot
    
    def get_snapshot_count(self) -> int:
        """Get total snapshot count."""
        return len(list(config.SNAPSHOTS_DIR.glob("*.jpg")))

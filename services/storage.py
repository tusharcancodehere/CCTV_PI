"""Storage management for snapshots and recordings."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config.system_config import config


class StorageService:
    """Manages file storage for snapshots and recordings."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [config.SNAPSHOTS_DIR, config.RECORDINGS_DIR, 
                         config.LOGS_DIR, config.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_snapshot_filename(self) -> str:
        """Generate snapshot filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"snapshot_{timestamp}.jpg"
    
    def get_recording_filename(self) -> str:
        """Generate recording filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recording_{timestamp}.mp4"
    
    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Get list of recent snapshots (capped to 100)."""
        snapshots = []
        try:
            files = sorted(config.SNAPSHOTS_DIR.glob("*.jpg"), 
                           key=lambda f: f.stat().st_mtime,
                           reverse=True)[:100]
            for file_path in files:
                try:
                    stat = file_path.stat()
                    snapshots.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size_kb": stat.st_size / 1024,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except Exception:
                    pass
        except Exception:
            pass
        return snapshots
    
    def get_recordings(self) -> List[Dict[str, Any]]:
        """Get list of recent recordings (capped to 100)."""
        recordings = []
        try:
            files = sorted(config.RECORDINGS_DIR.glob("*.mp4"), 
                           key=lambda f: f.stat().st_mtime,
                           reverse=True)[:100]
            for file_path in files:
                try:
                    stat = file_path.stat()
                    recordings.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size_mb": stat.st_size / (1024 * 1024),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except Exception:
                    pass
        except Exception:
            pass
        return recordings
    
    def delete_snapshot(self, filename: str) -> bool:
        """Delete a snapshot."""
        try:
            file_path = config.SNAPSHOTS_DIR / filename
            if file_path.exists() and file_path.parent == config.SNAPSHOTS_DIR:
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def delete_recording(self, filename: str) -> bool:
        """Delete a recording."""
        try:
            file_path = config.RECORDINGS_DIR / filename
            if file_path.exists() and file_path.parent == config.RECORDINGS_DIR:
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        def get_dir_size(path: Path) -> int:
            total = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
            return total
        
        snapshots_size = get_dir_size(config.SNAPSHOTS_DIR)
        recordings_size = get_dir_size(config.RECORDINGS_DIR)
        
        return {
            "snapshots_mb": snapshots_size / (1024 * 1024),
            "recordings_mb": recordings_size / (1024 * 1024),
            "total_mb": (snapshots_size + recordings_size) / (1024 * 1024),
            "snapshot_count": len(list(config.SNAPSHOTS_DIR.glob("*.jpg"))),
            "recording_count": len(list(config.RECORDINGS_DIR.glob("*.mp4"))),
        }
    
    def cleanup_old_files(self, max_age_days: int = 7) -> None:
        """Remove files older than specified days."""
        import time
        now = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        for file_path in config.SNAPSHOTS_DIR.glob("*.jpg"):
            if now - file_path.stat().st_mtime > max_age_seconds:
                try:
                    file_path.unlink()
                except Exception:
                    pass
        
        for file_path in config.RECORDINGS_DIR.glob("*.mp4"):
            if now - file_path.stat().st_mtime > max_age_seconds:
                try:
                    file_path.unlink()
                except Exception:
                    pass


# Global instance
storage_service = StorageService()

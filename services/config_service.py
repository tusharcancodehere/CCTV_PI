"""Configuration service for runtime settings."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from config.system_config import config


class ConfigService:
    """Manages runtime configuration and settings."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self.settings_file = config.CACHE_DIR / "settings.json"
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from file."""
        self.settings = self._get_default_settings()
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    saved = json.load(f)
                    self.settings.update(saved)
            except Exception:
                pass
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            "resolution": list(config.CAMERA_RESOLUTION),
            "fps": config.CAMERA_FPS,
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "flip_horizontal": False,
            "flip_vertical": False,
            "rotate": 0,
            "mjpeg_quality": config.MJPEG_QUALITY,
            "enable_motion_detection": config.ENABLE_MOTION_DETECTION,
            "enable_face_detection": config.ENABLE_FACE_DETECTION,
            "enable_qr_detection": config.ENABLE_QR_DETECTION,
            "motion_threshold": 5,
            "theme": "dark",
            "auto_record": False,
            "record_quality": "medium",
            "mirror_preview": config.MIRROR_PREVIEW,
        }
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file."""
        try:
            self.settings.update(settings)
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception:
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a single setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a single setting."""
        self.settings[key] = value
        return self.save_settings({key: value})
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()
    
    def reset_settings(self) -> bool:
        """Reset to default settings."""
        self.settings = self._get_default_settings()
        return self.save_settings(self.settings)


# Global instance
config_service = ConfigService()

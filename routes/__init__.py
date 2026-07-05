"""Routes module."""

from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.streaming import streaming_bp

__all__ = [
    "dashboard_bp",
    "api_bp",
    "streaming_bp",
]

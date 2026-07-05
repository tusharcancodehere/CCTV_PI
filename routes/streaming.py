"""Streaming routes."""

from flask import Blueprint, Response
from camera import camera_manager
from services import logger_service

streaming_bp = Blueprint("streaming", __name__)
logger = logger_service.get_logger("streaming")


@streaming_bp.route("/video_feed", methods=["GET"])
def video_feed():
    """MJPEG video stream endpoint."""
    if not camera_manager.connected:
        return "Camera not connected", 503
    
    logger.debug("Video stream requested")
    
    return Response(
        camera_manager.get_stream_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@streaming_bp.route("/snapshot", methods=["GET"])
def snapshot():
    """Get current frame as JPEG snapshot."""
    try:
        jpeg = camera_manager.get_current_frame_jpeg()
        if jpeg is None:
            from camera.stream import get_fallback_jpeg
            jpeg = get_fallback_jpeg()
        return Response(jpeg, mimetype="image/jpeg")
    except Exception as e:
        logger.error(f"Snapshot route error: {e}")
        from camera.stream import get_fallback_jpeg
        return Response(get_fallback_jpeg(), mimetype="image/jpeg")

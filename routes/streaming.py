"""Streaming routes — MJPEG camera feed and snapshot endpoints."""

from flask import Blueprint, Response
from camera import camera_manager
from camera.stream import get_fallback_jpeg
from services import logger_service

streaming_bp = Blueprint("streaming", __name__)
logger = logger_service.get_logger("streaming")


@streaming_bp.route("/api/stream", methods=["GET"])
def video_feed():
    """MJPEG live camera stream.

    Always returns a valid multipart stream — falls back to an offline
    placeholder frame so the browser <img> tag never gets a broken image.
    """
    logger.debug("MJPEG stream requested")
    return Response(
        camera_manager.get_stream_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@streaming_bp.route("/video_feed", methods=["GET"])
def video_feed_legacy():
    """Legacy alias — keeps old bookmarks / integrations working."""
    return video_feed()


@streaming_bp.route("/snapshot", methods=["GET"])
def snapshot():
    """Return the current frame as a single JPEG image."""
    try:
        jpeg = camera_manager.get_current_frame_jpeg()
        if jpeg is None:
            jpeg = get_fallback_jpeg()
        return Response(jpeg, mimetype="image/jpeg")
    except Exception as exc:
        logger.error(f"Snapshot error: {exc}")
        return Response(get_fallback_jpeg(), mimetype="image/jpeg")

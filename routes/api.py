"""API routes for system status and operations."""

from flask import Blueprint, jsonify, request
from datetime import datetime

from camera import camera_manager
from services import (
    logger_service,
    system_monitor,
    analytics_service,
    storage_service,
)
from services.config_service import config_service

api_bp = Blueprint("api", __name__)
logger = logger_service.get_logger("api")


@api_bp.route("/status", methods=["GET"])
def get_status():
    """Get system status."""
    stats = system_monitor.get_stats(
        camera_connected=camera_manager.connected if camera_manager else False,
        camera_resolution=camera_manager.resolution if camera_manager else [640, 480]
    )
    
    return jsonify({
        "success": True,
        "data": system_monitor.to_dict(stats)
    })


@api_bp.route("/camera/status", methods=["GET"])
def camera_status():
    """Get camera status."""
    return jsonify({
        "success": True,
        "data": camera_manager.get_status()
    })


@api_bp.route("/camera/restart", methods=["POST"])
def camera_restart():
    """Restart camera."""
    try:
        if camera_manager.restart():
            analytics_service.increment_camera_restarts()
            logger.info("Camera restarted via API")
            return jsonify({"success": True, "message": "Camera restarted"})
        else:
            return jsonify({"success": False, "message": "Failed to restart camera"}), 500
    except Exception as e:
        logger.error(f"Camera restart error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/snapshot/capture", methods=["POST"])
def capture_snapshot():
    """Capture a snapshot."""
    try:
        path = camera_manager.capture_snapshot()
        if path:
            analytics_service.increment_snapshots()
            logger.info("Snapshot captured via API")
            return jsonify({"success": True, "path": path})
        else:
            return jsonify({"success": False, "message": "Failed to capture snapshot"}), 500
    except Exception as e:
        logger.error(f"Snapshot capture error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/recording/start", methods=["POST"])
def start_recording():
    """Start video recording."""
    try:
        if camera_manager.start_recording():
            logger.info("Recording started via API")
            return jsonify({"success": True, "message": "Recording started"})
        else:
            return jsonify({"success": False, "message": "Failed to start recording"}), 500
    except Exception as e:
        logger.error(f"Recording start error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/recording/stop", methods=["POST"])
def stop_recording():
    """Stop video recording."""
    try:
        result = camera_manager.stop_recording()
        if result:
            logger.info("Recording stopped via API")
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"success": False, "message": "No active recording"}), 400
    except Exception as e:
        logger.error(f"Recording stop error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/recording/status", methods=["GET"])
def recording_status():
    """Get recording status."""
    try:
        is_rec = camera_manager.is_recording()
        duration = camera_manager.recorder.get_recording_duration() if is_rec else 0.0
        return jsonify({
            "success": True,
            "recording": is_rec,
            "duration_seconds": duration
        })
    except Exception as e:
        logger.error(f"Recording status error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/analytics", methods=["GET"])
def get_analytics():
    """Get analytics data."""
    try:
        return jsonify({
            "success": True,
            "data": analytics_service.get_analytics()
        })
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/logs", methods=["GET"])
def get_logs():
    """Get recent logs."""
    try:
        limit = request.args.get("limit", 50, type=int)
        logs = logger_service.get_recent_logs()[-limit:]
        return jsonify({
            "success": True,
            "logs": logs
        })
    except Exception as e:
        logger.error(f"Logs endpoint error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/storage", methods=["GET"])
def get_storage():
    """Get storage usage."""
    try:
        snapshots = storage_service.get_snapshots()
        recordings = storage_service.get_recordings()
        usage = storage_service.get_storage_usage()
        return jsonify({
            "success": True,
            "usage": usage,
            "snapshots": snapshots,
            "recordings": recordings
        })
    except Exception as e:
        logger.error(f"Storage endpoint error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/settings", methods=["GET"])
def get_settings():
    """Get all settings."""
    try:
        return jsonify({
            "success": True,
            "data": config_service.get_all_settings()
        })
    except Exception as e:
        logger.error(f"Settings get error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/settings", methods=["POST"])
def update_settings():
    """Update settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        if config_service.save_settings(data):
            # Dynamically apply settings to the camera manager
            camera_manager.apply_settings(data)
            logger.info(f"Settings updated and applied via API: {list(data.keys())}")
            return jsonify({"success": True, "message": "Settings saved and applied"})
        else:
            return jsonify({"success": False, "message": "Failed to save settings"}), 500
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/performance/estimate", methods=["POST"])
def get_performance_estimate():
    """Get estimated performance metrics for configuration."""
    try:
        data = request.get_json() or {}
        resolution = data.get("resolution", [640, 480])
        fps = data.get("fps", 30)
        device_profile = data.get("device_profile")
        
        from services.performance_estimator import performance_estimator
        if not device_profile:
            device_profile = performance_estimator.auto_detect_device()
            
        res_tuple = (resolution[0], resolution[1])
        est = performance_estimator.estimate(res_tuple, fps, device_profile)
        return jsonify({"success": True, "data": est})
    except Exception as e:
        logger.error(f"Error calculating performance estimate: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/performance/suggest", methods=["GET"])
def get_performance_suggestion():
    """Get recommended camera configuration based on current resources."""
    try:
        from services.performance_estimator import performance_estimator
        suggestion = performance_estimator.auto_suggest()
        return jsonify({"success": True, "data": suggestion})
    except Exception as e:
        logger.error(f"Error getting performance suggestion: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/snapshot/file/<filename>", methods=["GET"])
def get_snapshot_file(filename):
    """Serve a saved snapshot file."""
    try:
        from flask import send_from_directory
        from config.system_config import config
        # Security check: prevent directory traversal
        if "/" in filename or "\\" in filename or ".." in filename:
            return "Invalid filename", 400
        return send_from_directory(config.SNAPSHOTS_DIR, filename)
    except Exception as e:
        logger.error(f"Error serving snapshot file {filename}: {e}")
        return "File not found", 404


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

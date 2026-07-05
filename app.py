"""Main Flask application — single entry point."""

import sys
import logging

try:
    from flask import Flask
except ImportError:
    print("CRITICAL: Flask not installed. Run ./setup.sh first.")
    sys.exit(1)

from config.system_config import config
from services import logger_service, analytics_service
from camera import camera_manager


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["JSON_SORT_KEYS"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # Disable static file caching

    logger = logger_service.get_logger("app")

    # Register all blueprints
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    from routes.streaming import streaming_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(streaming_bp)

    # Start background analytics + watchdog
    analytics_service.start()

    # Start camera (gracefully degrade if hardware missing)
    try:
        if camera_manager.start():
            logger.info("Camera initialized and streaming")
        else:
            logger.warning("Camera unavailable — running in offline mode")
    except Exception as exc:
        logger.error(f"Camera startup error: {exc} — running in offline mode")

    # Register cleanup
    import atexit
    @atexit.register
    def _shutdown():
        logger.info("Shutting down services…")
        camera_manager.stop()
        analytics_service.stop()

    logger.info(f"OpenCV Vision Dashboard started → http://{config.HOST}:{config.PORT}")
    return app


if __name__ == "__main__":
    app = create_app()
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False,
            threaded=True,
        )
    except KeyboardInterrupt:
        print("\nShutting down…")

"""Main Flask application."""

import logging
from flask import Flask, render_template, jsonify
from datetime import datetime

from config import config, LogLevel
from services import logger_service, system_monitor, analytics_service
from camera import camera_manager


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    # Configuration
    app.config["JSON_SORT_KEYS"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    
    # Initialize logging
    logger = logger_service.get_logger("app")
    
    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    from routes.streaming import streaming_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(streaming_bp)
    
    # Initialize and start background services
    analytics_service.start()
    if camera_manager.start():
        logger.info("Camera initialized and started")
    else:
        logger.error("Failed to initialize camera")
        
    # Bulletproof cleanup on shutdown
    import atexit
    @atexit.register
    def cleanup():
        logger.info("Shutting down background services...")
        camera_manager.stop()
        analytics_service.stop()
    
    logger.info(f"OpenCV Vision Dashboard started on port {config.PORT}")
    
    return app


if __name__ == "__main__":
    app = create_app()
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down...")

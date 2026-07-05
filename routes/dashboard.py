"""Dashboard routes."""

from flask import Blueprint, render_template
from services import logger_service

dashboard_bp = Blueprint("dashboard", __name__)
logger = logger_service.get_logger("dashboard")


@dashboard_bp.route("/", methods=["GET"])
def dashboard():
    """Main dashboard page."""
    logger.debug("Dashboard requested")
    return render_template("dashboard.html")


@dashboard_bp.route("/about", methods=["GET"])
def about():
    """About page."""
    return render_template("about.html")

"""API Package for Book Buddy."""
from __future__ import annotations

from flask import Flask

def install_api(app: Flask) -> None:
    """Register all REST API endpoints."""
    from .v1 import api_v1_bp
    app.register_blueprint(api_v1_bp)

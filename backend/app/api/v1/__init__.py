"""API v1 Package and Master Blueprint."""
from __future__ import annotations

from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

from .csrf import csrf_bp
from .auth import auth_bp
from .books import books_bp
from .checkout import checkout_bp
from .memberships import memberships_bp
from .events import events_bp
from .gallery import gallery_bp
from .collaborators import collaborators_bp
from .media import media_bp
from .contact import contact_bp

# Register all child blueprints onto the /api/v1 prefix
api_v1_bp.register_blueprint(csrf_bp)
api_v1_bp.register_blueprint(auth_bp)
api_v1_bp.register_blueprint(books_bp)
api_v1_bp.register_blueprint(checkout_bp)
api_v1_bp.register_blueprint(memberships_bp)
api_v1_bp.register_blueprint(events_bp)
api_v1_bp.register_blueprint(gallery_bp)
api_v1_bp.register_blueprint(collaborators_bp)
api_v1_bp.register_blueprint(media_bp)
api_v1_bp.register_blueprint(contact_bp)

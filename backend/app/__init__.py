"""Book Buddy Flask Application Package."""
from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SERVICES_DIR = APP_DIR / "services"
ROUTES_DIR = APP_DIR / "routes"
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
BASE_DIR = APP_DIR

for p in (str(SERVICES_DIR), str(ROUTES_DIR), str(APP_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from .config import DATABASE_PATH, ROOT_DIR, get_database_path
from .db import get_db, db_connection, close_db
from .routes.site import *

def create_app(test_config=None):
    from .routes import site as site_module
    _app = site_module.app
    if test_config:
        _app.config.update(test_config)
    return _app

app = create_app()

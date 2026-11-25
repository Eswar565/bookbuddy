"""SPA (Single Page Application) Serving and Fallback.

Serves built React assets from frontend/dist when present, with correct
caching headers and SPA fallback to index.html for non-API/non-admin routes.
"""

from __future__ import annotations

import os
from pathlib import Path
from flask import Flask, Response, send_from_directory, request

def install_spa_serving(app: Flask, base_dir: Path) -> None:
    frontend_dist = base_dir / "frontend" / "dist"
    frontend_assets = frontend_dist / "assets"

    @app.route("/assets/<path:filename>")
    def serve_frontend_assets(filename: str):
        if frontend_assets.exists():
            response = send_from_directory(str(frontend_assets), filename)
            # Long-term immutable caching for hashed production assets
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response
        return "Asset not found", 404

    @app.route("/vite.svg")
    def serve_vite_svg():
        if (frontend_dist / "vite.svg").exists():
            return send_from_directory(str(frontend_dist), "vite.svg")
        return "Not found", 404

    def serve_spa_index():
        if not (frontend_dist / "index.html").exists():
            return "React frontend build not found. Run 'npm run build' in frontend/.", 404
        response = send_from_directory(str(frontend_dist), "index.html")
        # Ensure fresh index.html is always requested so new asset hashes are loaded
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # Dedicated preview route for React SPA regardless of USE_REACT flag
    @app.route("/react", defaults={"subpath": ""})
    @app.route("/react/<path:subpath>")
    def preview_react_spa(subpath: str):
        return serve_spa_index()

    # When USE_REACT=1, use SPA fallback for public non-API, non-admin routes
    @app.before_request
    def react_spa_router():
        if os.environ.get("USE_REACT", "0") != "1":
            return None

        path = request.path.lower()
        # Reserved backend prefixes that MUST NEVER be handled by SPA
        exempt_prefixes = (
            "/api/",
            "/admin/",
            "/static/",
            "/media/",
            "/assets/",
            "/library/export/",
            "/favicon.ico",
            "/vite.svg",
            "/robots.txt",
            "/sitemap.xml",
        )
        if any(path.startswith(prefix) for prefix in exempt_prefixes) or path == "/favicon.ico":
            return None

        # Serve React SPA index for public pages
        if request.method in ("GET", "HEAD"):
            return serve_spa_index()

        return None

    @app.after_request
    def set_spa_cache_headers(response: Response):
        if request.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            if "X-Robots-Tag" in response.headers:
                del response.headers["X-Robots-Tag"]
        return response

    # Place react_spa_router ahead of legacy dynamic page dispatchers
    funcs = app.before_request_funcs.get(None, [])
    if react_spa_router in funcs:
        funcs.remove(react_spa_router)
        funcs.insert(1, react_spa_router)

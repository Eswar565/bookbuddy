import os
from pathlib import Path
import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

def test_react_preview_route_and_headers(client):
    # /react should always serve the React SPA index
    res = client.get("/react")
    assert res.status_code == 200
    assert b'<div id="root"></div>' in res.data
    assert "no-cache" in res.headers.get("Cache-Control", "")

def test_spa_assets_serving_and_caching(client):
    # Find an asset in frontend/dist/assets
    assets_dir = Path(flask_app.root_path) / "frontend" / "dist" / "assets"
    if assets_dir.exists():
        files = list(assets_dir.glob("*.js"))
        if files:
            asset_name = files[0].name
            res = client.get(f"/assets/{asset_name}")
            assert res.status_code == 200
            assert "immutable" in res.headers.get("Cache-Control", "")

def test_legacy_templates_served_by_default(client):
    # By default (USE_REACT=0), the Jinja site is served
    os.environ.pop("USE_REACT", None)
    res = client.get("/")
    assert res.status_code == 200
    # Jinja template has specific navbar or structure
    assert b"Book Buddy" in res.data

def test_use_react_flag_serves_spa(client, monkeypatch):
    monkeypatch.setenv("USE_REACT", "1")
    
    # Homepage serves SPA
    res = client.get("/")
    assert res.status_code == 200
    assert b'<div id="root"></div>' in res.data
    assert "no-cache" in res.headers.get("Cache-Control", "")

    # Subroute serves SPA fallback
    res = client.get("/about")
    assert res.status_code == 200
    assert b'<div id="root"></div>' in res.data

    # Admin route is NOT intercepted by SPA
    admin_res = client.get("/admin/login/")
    assert admin_res.status_code == 200
    assert b'<div id="root"></div>' not in admin_res.data
    assert b"Admin" in admin_res.data or b"Login" in admin_res.data or b"password" in admin_res.data

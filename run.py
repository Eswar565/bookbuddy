import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
for p in (str(BACKEND_DIR), str(BACKEND_DIR / "app"), str(BACKEND_DIR / "app" / "services")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("APP_ENV", "development")

from app import app, get_database_path

if __name__ == "__main__":
    db_file = get_database_path()
    port = int(os.environ.get("PORT") or os.environ.get("FLASK_PORT") or 5000)
    print(f"Starting Book Buddy [{os.environ.get('APP_ENV')}] on port {port} (Database: {db_file})")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )

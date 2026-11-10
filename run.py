import os

# Default to development environment for local server runs if not set
os.environ.setdefault("APP_ENV", "development")

from app import app, get_database_path


if __name__ == "__main__":
    db_file = get_database_path()
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Book Buddy [{os.environ.get('APP_ENV')}] on port {port} (Database: {db_file})")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )



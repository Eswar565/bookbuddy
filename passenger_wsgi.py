"""cPanel Passenger entry point."""
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parent)
backend = str(Path(__file__).resolve().parent / "backend")
services = str(Path(__file__).resolve().parent / "backend" / "app" / "services")
for p in (backend, services, root):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import app as application

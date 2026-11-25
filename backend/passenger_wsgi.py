"""cPanel Passenger entry point."""
import sys
from pathlib import Path

backend = str(Path(__file__).resolve().parent)
root = str(Path(__file__).resolve().parent.parent)
services = str(Path(__file__).resolve().parent / "app" / "services")
for p in (backend, services, root):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import app as application

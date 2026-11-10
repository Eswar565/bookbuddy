"""cPanel Passenger entry point. Configure Python and environment in cPanel."""
import sys
from pathlib import Path
root = str(Path(__file__).resolve().parent)
if root not in sys.path:
    sys.path.insert(0, root)
from app import app as application

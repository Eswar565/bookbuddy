import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app

for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if rule.rule.startswith('/admin/'):
        methods = list(rule.methods - {"OPTIONS", "HEAD"})
        print(f"{rule.rule} -> {rule.endpoint} {methods}")

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = Path('backups') / timestamp
backup_dir.mkdir(parents=True, exist_ok=True)

# 1. Back up all SQLite database files (root and instance)
dbs = list(Path('.').glob('*.db')) + list(Path('.').glob('*.sqlite*')) + list(Path('instance').glob('*.sqlite*')) + list(Path('instance').glob('*.db'))
for db in dbs:
    dest = backup_dir / db.name
    shutil.copy2(db, dest)
    print(f"DATABASE_BACKUP: {dest.resolve()} ({dest.stat().st_size} bytes)")

# 2. Create clean zip of project files
zip_path = Path('backups') / f"bookbuddy_backup_{timestamp}.zip"
ignore_dirs = {'.pytest_cache', '__pycache__', 'backups', '.git', '.venv', 'venv'}

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            file_path = Path(root) / f
            if file_path.suffix == '.pyc' or file_path == zip_path:
                continue
            arcname = file_path.relative_to('.')
            zf.write(file_path, arcname)

print(f"PROJECT_ZIP: {zip_path.resolve()} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")

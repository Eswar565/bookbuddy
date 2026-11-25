#!/usr/bin/env python3
"""Reset the demo database and media directory from a saved snapshot before a client demo."""

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def reset_demo(snapshot_path: Path, target_path: Path, media_snapshot_zip: Path, media_target: Path):
    if not snapshot_path.exists():
        sys.exit(f"Error: Snapshot database not found at {snapshot_path}. Run tools/make_demo_data.py first.")

    print("=" * 60)
    print("RESETTING DEMO ENVIRONMENT TO CLEAN SNAPSHOT")
    print("=" * 60)

    # 1. Reset Database
    print(f"Restoring database:\n  From: {snapshot_path}\n  To:   {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()
    shutil.copy2(snapshot_path, target_path)
    print("Database restored successfully.")

    # 2. Reset Media
    if media_snapshot_zip.exists():
        print(f"\nRestoring media directory:\n  From: {media_snapshot_zip}\n  To:   {media_target}")
        media_target.mkdir(parents=True, exist_ok=True)
        # Extract files from snapshot zip
        with zipfile.ZipFile(media_snapshot_zip, "r") as zf:
            zf.extractall(media_target)
        print("Media restored successfully.")
    else:
        print(f"\nMedia snapshot {media_snapshot_zip} not found; skipping media reset.")

    print("\nDEMO RESET COMPLETE. Ready for client demonstration.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset demo database and media from snapshot.")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "instance" / "demo_snapshot.sqlite3", help="Source demo snapshot")
    
    # Default target DB: check environment variable BOOK_BUDDY_DATABASE, then demo db, then standard db
    env_db = os.environ.get("BOOK_BUDDY_DATABASE")
    if env_db:
        default_target = Path(env_db)
    elif (ROOT / "instance" / "book_buddy_demo.sqlite3").exists():
        default_target = ROOT / "instance" / "book_buddy_demo.sqlite3"
    else:
        default_target = ROOT / "instance" / "book_buddy.sqlite3"

    parser.add_argument("--target", type=Path, default=default_target, help="Target database to reset")
    parser.add_argument("--media-snapshot", type=Path, default=ROOT / "backups" / "demo_media_snapshot.zip", help="Source media snapshot zip")
    
    env_media = os.environ.get("MEDIA_ROOT")
    default_media = Path(env_media) if env_media else ROOT / "media"
    parser.add_argument("--media-target", type=Path, default=default_media, help="Target media folder to restore into")

    args = parser.parse_args()
    reset_demo(args.snapshot, args.target, args.media_snapshot, args.media_target)


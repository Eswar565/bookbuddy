#!/usr/bin/env python3
"""Create a clean demo database and snapshot from the current database.

Never modifies the original database file.
"""

import argparse
import datetime
import os
import secrets
import shutil
import sqlite3
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def make_demo_data(source_db_path: Path, target_db_path: Path, snapshot_db_path: Path, media_source: Path, media_snapshot_zip: Path):
    if not source_db_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_db_path}")

    print(f"--- 1. Copying source database to target: {target_db_path} ---")
    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    if target_db_path.exists():
        target_db_path.unlink()
    shutil.copy2(source_db_path, target_db_path)

    con = sqlite3.connect(target_db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    existing_tables = set(r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())

    # Tables to clear completely
    tables_to_clear = [
        "admin_audit",
        "admin_notifications",
        "notification_reads",
        "notifications17",
        "contact_submissions",
        "partner_submissions",
        "reader_contributions",
        "subscribers",
        "event_registrations",
        "orders",
        "order_items",
        "payments17",
        "payment_webhooks",
        "lending_subscriptions",
        "memberships",
        "lending_loans",
        "copies17",
        "reservations17",
        "fines17",
        "fine_payments17",
        "book_requests",
        "mail_queue17",
        "auth_tokens17",
        "rate_limits17",
        "presence17",
        "conversations17",
        "conversation_members17",
        "messages17",
        "coupon_uses17",
        "users",
        "admin_users",
    ]

    cleared_counts = {}
    for tbl in tables_to_clear:
        if tbl in existing_tables:
            cnt = cur.execute(f"SELECT count(*) FROM \"{tbl}\"").fetchone()[0]
            cleared_counts[tbl] = cnt
            cur.execute(f"DELETE FROM \"{tbl}\"")

    # Clean test rows from gallery_items (e.g. ID 1 with missing file)
    removed_gallery_count = 0
    if "gallery_items" in existing_tables:
        res = cur.execute("DELETE FROM gallery_items WHERE id = 1 OR title IN ('demo', 'test')")
        removed_gallery_count = res.rowcount

    # Tables to keep
    tables_to_keep = [
        "site_content",
        "site_navigation",
        "homepage_sections",
        "books",
        "events",
        "event_coupons",
        "coupons17",
        "publications",
        "gallery_items",
        "lending_plans",
        "plans",
        "branches17",
        "access_rules",
        "app_flags",
        "schema_updates",
        "content_visibility",
        "page_heroes",
        "page_sections23",
        "cms_pages",
    ]

    kept_counts = {}
    for tbl in tables_to_keep:
        if tbl in existing_tables:
            cnt = cur.execute(f"SELECT count(*) FROM \"{tbl}\"").fetchone()[0]
            kept_counts[tbl] = cnt

    # Create demo admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@BookBuddy2026!")
    admin_hash = generate_password_hash(admin_password)

    cur.execute(
        "INSERT INTO admin_users (email, name, role, is_active, password_hash) VALUES (?, ?, ?, 1, ?)",
        (admin_email, "Demo Administrator", "super_admin", admin_hash),
    )
    admin_id = cur.lastrowid

    # Create demo member
    member_email = "demo.member@example.com"
    member_name = "Demo Member"
    member_password = secrets.token_urlsafe(12)
    member_hash = generate_password_hash(member_password)

    cur.execute(
        "INSERT INTO users (email, name, password_hash, is_active, session_version) VALUES (?, ?, ?, 1, 1)",
        (member_email, member_name, member_hash),
    )
    member_id = cur.lastrowid

    # Give demo member an active 3-month subscription
    today = datetime.date.today()
    starts_on = (today - datetime.timedelta(days=1)).isoformat()
    expires_on = (today + datetime.timedelta(days=90)).isoformat()
    plan_row = cur.execute("SELECT id, amount FROM lending_plans WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
    if plan_row:
        plan_id, plan_amount = plan_row["id"], plan_row["amount"]
        cur.execute(
            """INSERT INTO lending_subscriptions
               (user_id, plan_id, status, starts_on, expires_on, payment_status, amount, book_limit_snapshot, duration_snapshot)
               VALUES (?, ?, 'Active', ?, ?, 'Paid - confirmed by staff', ?, 3, 90)""",
            (member_id, plan_id, starts_on, expires_on, plan_amount or 1100),
        )

    con.commit()
    con.execute("VACUUM")
    con.close()

    # Create snapshot DB copy
    print(f"--- 2. Creating demo database snapshot: {snapshot_db_path} ---")
    snapshot_db_path.parent.mkdir(parents=True, exist_ok=True)
    if snapshot_db_path.exists():
        snapshot_db_path.unlink()
    shutil.copy2(target_db_path, snapshot_db_path)

    # Create media snapshot zip
    if media_source.exists():
        print(f"--- 3. Creating media snapshot: {media_snapshot_zip} ---")
        media_snapshot_zip.parent.mkdir(parents=True, exist_ok=True)
        zip_base = str(media_snapshot_zip).removesuffix(".zip")
        shutil.make_archive(zip_base, "zip", str(media_source))

    # Print summary
    print("\n" + "=" * 60)
    print("DEMO DATABASE CREATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Original DB (Untouched): {source_db_path}")
    print(f"Clean Demo DB:           {target_db_path}")
    print(f"Demo DB Snapshot:        {snapshot_db_path}")
    if media_snapshot_zip.exists():
        print(f"Demo Media Snapshot:     {media_snapshot_zip}")

    print("\n[REMOVED PERSONAL / TRANSACTIONAL DATA]")
    for tbl, count in sorted(cleared_counts.items()):
        if count > 0:
            print(f"  - {tbl:<24}: {count} records cleared")
    if removed_gallery_count:
        print(f"  - gallery_items test rows: {removed_gallery_count} cleared")

    print("\n[PRESERVED CATALOGUE & SETTINGS]")
    for tbl, count in sorted(kept_counts.items()):
        print(f"  - {tbl:<24}: {count} records kept")

    print("\n" + "-" * 60)
    print("DEMO CREDENTIALS (SAVE THESE - Member password shown ONCE):")
    print("-" * 60)
    print("1. Demo Administrator:")
    print(f"   Email:    {admin_email}")
    print(f"   Password: {admin_password}")
    print(f"   URL:      /admin/login/")
    print("\n2. Demo Member (Reader Account with Active Subscription):")
    print(f"   Email:    {member_email}")
    print(f"   Password: {member_password}")
    print(f"   URL:      /accounts/login/")
    print("=" * 60 + "\n")

    return {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "member_email": member_email,
        "member_password": member_password,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a clean demo database from production/dev database.")
    parser.add_argument("--source", type=Path, default=None, help="Source database to copy from")
    parser.add_argument("--target", type=Path, default=ROOT / "instance" / "book_buddy_demo.sqlite3", help="Target demo database")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "instance" / "demo_snapshot.sqlite3", help="Demo snapshot path")
    parser.add_argument("--media-source", type=Path, default=ROOT / "media", help="Source media folder")
    parser.add_argument("--media-snapshot", type=Path, default=ROOT / "backups" / "demo_media_snapshot.zip", help="Media snapshot zip")

    args = parser.parse_args()

    # Determine default source db
    source = args.source
    if not source:
        if (ROOT / "instance" / "book_buddy.sqlite3").exists():
            source = ROOT / "instance" / "book_buddy.sqlite3"
        elif (ROOT / "instance" / "book_buddy_dev.sqlite3").exists():
            source = ROOT / "instance" / "book_buddy_dev.sqlite3"
        else:
            sys.exit("Error: No database found in instance/")

    make_demo_data(source, args.target, args.snapshot, args.media_source, args.media_snapshot)

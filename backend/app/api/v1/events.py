"""Events and registrations API endpoints."""
from __future__ import annotations

from datetime import datetime
from flask import Blueprint, jsonify, request, session
from ...db import get_db

events_bp = Blueprint("api_events", __name__)

@events_bp.get("/events")
def list_events():
    db = get_db()
    view = request.args.get("view", "current").strip().lower()
    event_type = request.args.get("type", "").strip().lower()
    chosen_date = request.args.get("date", "").strip()
    today = datetime.now().date().isoformat()

    query = "SELECT * FROM events WHERE (is_active=1 OR is_active IS NULL)"
    params = []

    if chosen_date:
        query += " AND event_date = ?"
        params.append(chosen_date)
    elif view == "past":
        query += " AND event_date < ?"
        params.append(today)
    elif view == "current":
        query += " AND event_date >= ?"
        params.append(today)

    cat_clause = ""
    if event_type in ("contest", "contests"):
        cat_clause = " AND LOWER(category) IN ('contest', 'contests')"
    elif event_type in ("reading-circle", "reading_circle", "reading-circles"):
        cat_clause = " AND LOWER(category) IN ('reading-circle', 'reading_circle', 'reading-circles')"
    elif event_type in ("upcoming", "event", "events", "workshop"):
        cat_clause = " AND (LOWER(category) IN ('upcoming', 'event', 'events', 'workshop') OR category IS NULL OR category = '')"

    query += cat_clause
    query += " ORDER BY event_date " + ("DESC" if view == "past" else "ASC") + ", event_time ASC"
    rows = db.execute(query, params).fetchall()
    events = [dict(r) for r in rows]
    for ev in events:
        ev["seats_left"] = max(0, int(ev.get("capacity") or 0) - int(ev.get("booked_seats") or 0))

    current_count = db.execute(
        "SELECT COUNT(*) FROM events WHERE (is_active=1 OR is_active IS NULL) AND event_date >= ?" + cat_clause,
        (today,)
    ).fetchone()[0]
    past_count = db.execute(
        "SELECT COUNT(*) FROM events WHERE (is_active=1 OR is_active IS NULL) AND event_date < ?" + cat_clause,
        (today,)
    ).fetchone()[0]

    return jsonify({
        "ok": True,
        "data": {
            "events": events,
            "count": len(events),
            "current_count": current_count,
            "past_count": past_count
        }
    })

@events_bp.get("/events/<int:event_id>")
def get_event(event_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM events WHERE id=? AND is_active=1", (event_id,)).fetchone()
    if not row:
        return jsonify({
            "ok": False,
            "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found." }
        }), 404

    ev = dict(row)
    ev["seats_left"] = max(0, int(ev.get("capacity") or 0) - int(ev.get("booked_seats") or 0))
    return jsonify({
        "ok": True,
        "data": {
            "event": ev
        }
    })

@events_bp.get("/events/calendar")
def get_calendar():
    db = get_db()
    rows = db.execute("SELECT * FROM events WHERE is_active=1 ORDER BY event_date ASC, event_time ASC").fetchall()
    calendar_map = {}
    for r in rows:
        d = dict(r)
        d_str = d.get("event_date")
        if d_str:
            calendar_map.setdefault(d_str, []).append(d)

    return jsonify({
        "ok": True,
        "data": {
            "calendar": calendar_map
        }
    })

@events_bp.post("/events/<int:event_id>/register")
def register_event(event_id: int):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=? AND is_active=1", (event_id,)).fetchone()
    if not event:
        return jsonify({
            "ok": False,
            "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found." }
        }), 404

    data = request.get_json(silent=True) or request.form.to_dict()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    seats = max(1, int(data.get("seats") or 1))

    if not name or not email:
        return jsonify({
            "ok": False,
            "error": { "code": "MISSING_INFO", "message": "Name and email are required." }
        }), 400

    capacity = int(event.get("capacity") or 0)
    booked = int(event.get("booked_seats") or 0)
    if capacity > 0 and (booked + seats) > capacity:
        return jsonify({
            "ok": False,
            "error": { "code": "EVENT_FULL", "message": "Not enough seats available." }
        }), 409

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = db.execute(
        """INSERT INTO event_registrations (event_id, name, email, phone, seats, registered_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (event_id, name, email, phone, seats, now_str)
    )
    db.execute("UPDATE events SET booked_seats = booked_seats + ? WHERE id=?", (seats, event_id))
    db.commit()

    return jsonify({
        "ok": True,
        "message": f"Successfully registered for '{event['title']}'.",
        "data": {
            "registration_id": cur.lastrowid,
            "event_id": event_id,
            "seats": seats
        }
    }), 201

"""Media and Publications API endpoints (Newspapers, Magazines, Podcasts)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, session
from ...db import get_db
from ...services.accounts import get_active_subscription

media_bp = Blueprint("api_media", __name__)


@media_bp.get("/media")
def list_media():
    """List publications, optionally filtered by tab/kind and access (free/paid)."""
    db = get_db()
    args = request.args

    tab = args.get("tab", "").strip().lower()
    kind = args.get("kind", "").strip().lower()
    chosen_kind = kind or tab

    # Map shorthand or plural names to canonical kind
    if chosen_kind in {"news", "newspaper", "newspapers"}:
        canonical_kind = "news"
    elif chosen_kind in {"magazine", "magazines"}:
        canonical_kind = "magazine"
    elif chosen_kind in {"podcast", "podcasts"}:
        canonical_kind = "podcast"
    else:
        canonical_kind = "all"

    access_filter = args.get("access", "").strip().lower()
    conditions = ["is_active = 1"]
    params = []

    if access_filter == "free":
        conditions.append("is_paid = 0")
    elif access_filter == "paid":
        conditions.append("is_paid = 1")

    base_where = " AND ".join(conditions)

    if canonical_kind != "all":
        query = f"SELECT * FROM publications WHERE {base_where} AND kind = ? ORDER BY published_on DESC, id DESC"
        params.append(canonical_kind)
        rows = db.execute(query, params).fetchall()
        items = [dict(r) for r in rows]
        return jsonify({
            "ok": True,
            "data": {
                "kind": canonical_kind,
                "count": len(items),
                "items": items,
            }
        })

    # Return grouped results
    newspapers = [dict(r) for r in db.execute(
        f"SELECT * FROM publications WHERE {base_where} AND kind = 'news' ORDER BY published_on DESC, id DESC",
        params
    ).fetchall()]
    magazines = [dict(r) for r in db.execute(
        f"SELECT * FROM publications WHERE {base_where} AND kind = 'magazine' ORDER BY published_on DESC, id DESC",
        params
    ).fetchall()]
    podcasts = [dict(r) for r in db.execute(
        f"SELECT * FROM publications WHERE {base_where} AND kind = 'podcast' ORDER BY published_on DESC, id DESC",
        params
    ).fetchall()]

    return jsonify({
        "ok": True,
        "data": {
            "counts": {
                "newspapers": len(newspapers),
                "magazines": len(magazines),
                "podcasts": len(podcasts),
                "total": len(newspapers) + len(magazines) + len(podcasts),
            },
            "newspapers": newspapers,
            "magazines": magazines,
            "podcasts": podcasts,
        }
    })


@media_bp.get("/media/<int:pub_id>")
def get_media_item(pub_id: int):
    """Retrieve details and access status for a single publication."""
    db = get_db()
    row = db.execute("SELECT * FROM publications WHERE id = ? AND is_active = 1", (pub_id,)).fetchone()
    if not row:
        return jsonify({
            "ok": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Publication with id {pub_id} not found"
            }
        }), 404

    item = dict(row)
    user_id = session.get("user_id")

    can_access = True
    access_reason = "ALLOWED"

    if bool(item.get("is_paid")):
        if not user_id:
            can_access = False
            access_reason = "LOGIN_REQUIRED"
        else:
            sub = get_active_subscription(db, user_id)
            if not sub:
                can_access = False
                access_reason = "SUBSCRIPTION_REQUIRED"

    return jsonify({
        "ok": True,
        "data": {
            "publication": item,
            "access": {
                "can_access": can_access,
                "reason": access_reason,
                "is_paid": bool(item.get("is_paid")),
            }
        }
    })

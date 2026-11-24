# routes/locations.py
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from models.db import get_db_cursor
from services.geo_service import haversine_meters, build_geofence_reminder

locations_bp = Blueprint("locations", __name__)


@locations_bp.route("/locations")
@login_required
def locations_page():
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM saved_locations WHERE user_id = %s ORDER BY created_at DESC", (session["user_id"],))
        locations = cur.fetchall()
    return render_template("app/locations.html", locations=locations)


@locations_bp.route("/api/locations", methods=["POST"])
@login_required
def save_location():
    data = request.get_json(silent=True) or request.form
    radius = int(data.get("radius_meters", 250))
    if radius not in (100, 250, 500, 1000):
        radius = 250

    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO saved_locations
            (user_id, location_name, location_type, address_text, latitude, longitude, radius_meters, reminders_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                data["location_name"].strip(),
                data.get("location_type", "supermarket"),
                data["address_text"].strip(),
                float(data["latitude"]),
                float(data["longitude"]),
                radius,
                bool(data.get("reminders_enabled", True)),
            ),
        )
    return jsonify({"status": "saved"})


@locations_bp.route("/api/locations/check-proximity", methods=["POST"])
@login_required
def check_proximity():
    """
    Evaluates browser-supplied coordinates (only sent after explicit user permission)
    against saved store geofences with a 120-minute cooldown to prevent notification spam.
    """
    data = request.get_json(silent=True) or {}
    lat = float(data.get("latitude"))
    lon = float(data.get("longitude"))
    user_id = session["user_id"]

    triggered_alerts = []
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
        prefs = cur.fetchone() or {"reminder_cooldown_minutes": 120}
        cooldown_cutoff = datetime.utcnow() - timedelta(minutes=prefs["reminder_cooldown_minutes"])

        cur.execute(
            "SELECT * FROM saved_locations WHERE user_id = %s AND reminders_enabled = TRUE",
            (user_id,),
        )
        locations = cur.fetchall()

        cur.execute(
            """
            SELECT sl.recommended_budget, sl.planned_subtotal,
                   COUNT(sli.id) AS pending_items,
                   COALESCE(SUM(CASE WHEN sli.is_purchased THEN COALESCE(sli.actual_paid_price, sli.unit_price_snapshot) * sli.quantity ELSE 0 END), 0) AS actual_spent
            FROM shopping_lists sl
            LEFT JOIN shopping_list_items sli ON sli.shopping_list_id = sl.id AND sli.is_purchased = FALSE
            WHERE sl.user_id = %s AND sl.status IN ('active', 'locked')
            GROUP BY sl.id
            ORDER BY sl.updated_at DESC LIMIT 1
            """,
            (user_id,),
        )
        active = cur.fetchone() or {"recommended_budget": 0, "planned_subtotal": 0, "pending_items": 0, "actual_spent": 0}

        for loc in locations:
            dist = haversine_meters(lat, lon, float(loc["latitude"]), float(loc["longitude"]))
            if dist <= loc["radius_meters"]:
                cur.execute(
                    """
                    SELECT id FROM location_reminder_logs
                    WHERE user_id = %s AND location_id = %s AND triggered_at >= %s
                    """,
                    (user_id, loc["id"], cooldown_cutoff),
                )
                if cur.fetchone():
                    continue  # Cooldown active

                msg = build_geofence_reminder(
                    location_name=loc["location_name"],
                    pending_count=int(active["pending_items"]),
                    recommended_budget=float(active["recommended_budget"]),
                    budget_exceeded=float(active["actual_spent"]) > float(active["planned_subtotal"]) > 0,
                )
                cur.execute(
                    """
                    INSERT INTO location_reminder_logs (user_id, location_id, distance_meters, message_sent)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, loc["id"], round(dist, 2), msg),
                )
                triggered_alerts.append({"location": loc["location_name"], "distance_m": round(dist), "message": msg})

    return jsonify({"alerts": triggered_alerts})
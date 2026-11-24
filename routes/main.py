# routes/main.py, routes/budget.py, routes/insights.py
from flask import Blueprint, render_template, session
from routes.auth import login_required
from models.db import get_db_cursor

main_bp = Blueprint("main", __name__)
budget_bp = Blueprint("budget", __name__)
insights_bp = Blueprint("insights", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM shopping_lists WHERE user_id = %s AND status IN ('active', 'locked') ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        )
        active_list = cur.fetchone()
        items = []
        if active_list:
            cur.execute(
                """
                SELECT sli.*, p.name, p.tier_category, b.name AS brand_name
                FROM shopping_list_items sli
                JOIN products p ON sli.product_id = p.id
                JOIN brands b ON p.brand_id = b.id
                WHERE sli.shopping_list_id = %s
                """,
                (active_list["id"],),
            )
            items = cur.fetchall()

        cur.execute("SELECT * FROM saved_locations WHERE user_id = %s LIMIT 4", (user_id,))
        locations = cur.fetchall()

        cur.execute("SELECT * FROM purchase_history WHERE user_id = %s ORDER BY purchased_at DESC LIMIT 5", (user_id,))
        history = cur.fetchall()

        cur.execute("SELECT COUNT(*) AS wish_count FROM wishlist WHERE user_id = %s", (user_id,))
        wish_count = cur.fetchone()["wish_count"]

    return render_template(
        "app/dashboard.html",
        active_list=active_list,
        items=items,
        locations=locations,
        history=history,
        wish_count=wish_count,
    )


@budget_bp.route("/budget")
@login_required
def budget_view():
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM shopping_lists WHERE user_id = %s AND status IN ('active', 'locked') ORDER BY updated_at DESC LIMIT 1",
            (session["user_id"],),
        )
        active_list = cur.fetchone()
    return render_template("app/budget.html", active_list=active_list)


@insights_bp.route("/insights")
@login_required
def insights_view():
    user_id = session["user_id"]
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT DATE_FORMAT(purchased_at, '%Y-%m') AS month_key,
                   SUM(planned_subtotal) AS planned_total,
                   SUM(actual_expenditure) AS actual_total
            FROM purchase_history
            WHERE user_id = %s
            GROUP BY month_key
            ORDER BY month_key ASC
            """,
            (user_id,),
        )
        monthly_series = cur.fetchall()

        cur.execute(
            """
            SELECT p.tier_category, COUNT(*) AS count
            FROM purchase_items pi
            JOIN purchase_history ph ON pi.purchase_id = ph.id
            JOIN products p ON pi.product_id = p.id
            WHERE ph.user_id = %s
            GROUP BY p.tier_category
            """,
            (user_id,),
        )
        tier_breakdown = cur.fetchall()

    return render_template(
        "app/insights.html",
        monthly_series=monthly_series,
        tier_breakdown=tier_breakdown,
    )
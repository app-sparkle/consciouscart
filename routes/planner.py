import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from models.db import get_db_cursor
from routes.auth import login_required
from services.scoring_engine import compute_product_score
from services.budget_service import calculate_shopping_budget

planner_bp = Blueprint("planner", __name__)

TIER_ORDER = {
    "premium_organic": 1,
    "conscious_choice": 2,
    "budget_conscious": 3,
    "economy_choice": 4,
}


def fetch_four_alternatives(keyword: str) -> list[dict]:
    like_term = f"%{keyword.strip().lower()}%"
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT p.*, b.name AS brand_name, b.transparency_rating,
                   c.name AS category_name, pp.unit_price
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN product_categories c ON p.category_id = c.id
            JOIN product_prices pp ON pp.product_id = p.id AND pp.is_current = TRUE
            WHERE LOWER(p.search_keyword) LIKE %s OR LOWER(p.name) LIKE %s
            LIMIT 12
            """,
            (like_term, like_term),
        )
        rows = cur.fetchall()

        # Select one representative per tier (4 alternatives total)
        by_tier = {}
        for row in rows:
            tier = row["tier_category"]
            if tier not in by_tier:
                cur.execute("SELECT * FROM organic_certifications WHERE product_id = %s", (row["id"],))
                row["certifications"] = cur.fetchall()
                cur.execute(
                    """
                    SELECT i.*, pi.position_order, pi.is_certified_organic_input, pi.verification_status
                    FROM product_ingredients pi
                    JOIN ingredients i ON pi.ingredient_id = i.id
                    WHERE pi.product_id = %s
                    ORDER BY pi.position_order ASC
                    """,
                    (row["id"],),
                )
                row["ingredients"] = cur.fetchall()
                by_tier[tier] = row

    alternatives = sorted(by_tier.values(), key=lambda x: TIER_ORDER.get(x["tier_category"], 99))
    peer_prices = [float(a["unit_price"]) for a in alternatives]

    for alt in alternatives:
        alt["score_data"] = compute_product_score(alt, peer_prices)

    return alternatives


def get_active_list_and_items(user_id: int, list_id=None) -> tuple[dict | None, list[dict]]:
    with get_db_cursor() as cur:
        if list_id:
            cur.execute(
                "SELECT * FROM shopping_lists WHERE id = %s AND user_id = %s AND status != 'archived'",
                (list_id, user_id),
            )
        else:
            cur.execute(
                "SELECT * FROM shopping_lists WHERE user_id = %s AND status != 'archived' ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            )
        active_list = cur.fetchone()

        items = []
        if active_list:
            cur.execute(
                """
                SELECT sli.id, sli.product_id, sli.quantity, sli.unit_price_snapshot,
                       sli.need_classification, p.name AS product_name,
                       (sli.quantity * sli.unit_price_snapshot) AS line_total
                FROM shopping_list_items sli
                JOIN products p ON sli.product_id = p.id
                WHERE sli.shopping_list_id = %s
                ORDER BY sli.id DESC
                """,
                (active_list["id"],),
            )
            items = cur.fetchall()

    return active_list, items


@planner_bp.route("/planner")
@login_required
def planner_view():
    keyword = (request.args.get("q") or "soap").strip()
    alternatives = fetch_four_alternatives(keyword) if keyword else []
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM product_categories ORDER BY id ASC")
        categories = cur.fetchall()
        cur.execute(
            "SELECT * FROM shopping_lists WHERE user_id = %s AND status != 'archived' ORDER BY updated_at DESC",
            (session["user_id"],),
        )
        lists = cur.fetchall()

    active_list, list_items = get_active_list_and_items(session["user_id"])
    return render_template(
        "app/planner.html",
        keyword=keyword,
        alternatives=alternatives,
        categories=categories,
        shopping_lists=lists,
        active_list=active_list,
        list_items=list_items,
    )


@planner_bp.route("/compare")
@login_required
def compare_view():
    keyword = (request.args.get("q") or "soap").strip()
    alternatives = fetch_four_alternatives(keyword)
    return render_template("app/compare.html", keyword=keyword, alternatives=alternatives)


@planner_bp.route("/api/list/add-with-verification", methods=["POST"])
@login_required
def add_item_with_verification():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id", 0))
    quantity = max(1, int(data.get("quantity", 1)))
    need_response = data.get("need_response")  # planned_need | occasional_purchase | just_browsing
    list_id = data.get("list_id")

    user_id = session["user_id"]

    # Responsible Consumption: "Just browsing" routes to Wishlist instead of Shopping List
    if need_response == "just_browsing":
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO wishlist (user_id, product_id, reason_note)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE reason_note = VALUES(reason_note)
                """,
                (user_id, product_id, "Marked as 'Just browsing' during Need Verification"),
            )
        return jsonify({
            "status": "wishlisted",
            "message": "Added to your Wishlist instead of your active shopping list so you can evaluate need without impulse spending.",
        })

    with get_db_cursor() as cur:
        if list_id:
            cur.execute("SELECT * FROM shopping_lists WHERE id = %s AND user_id = %s", (list_id, user_id))
        else:
            cur.execute(
                "SELECT * FROM shopping_lists WHERE user_id = %s AND status = 'active' ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            )
        active_list = cur.fetchone()
        if not active_list:
            cur.execute(
                "INSERT INTO shopping_lists (user_id, title, status) VALUES (%s, 'My Grocery Plan', 'active')",
                (user_id,),
            )
            active_list = {"id": cur.lastrowid, "is_locked": False}

        if active_list.get("is_locked"):
            return jsonify({"status": "locked", "message": "This shopping list is locked to prevent impulse additions."}), 409

        # Duplicate item & pantry stock check
        cur.execute("SELECT name, search_keyword FROM products WHERE id = %s", (product_id,))
        prod = cur.fetchone()
        if not prod:
            return jsonify({"status": "not_found", "message": "Product not found."}), 404

        cur.execute(
            "SELECT item_name, quantity_remaining, unit FROM pantry_items WHERE user_id = %s AND LOWER(item_name) LIKE %s",
            (user_id, f"%{prod['search_keyword'].lower()}%"),
        )
        pantry_match = cur.fetchone()

        cur.execute("SELECT unit_price FROM product_prices WHERE product_id = %s AND is_current = TRUE", (product_id,))
        price_row = cur.fetchone()
        unit_price = float(price_row["unit_price"])

        cur.execute(
            """
            INSERT INTO shopping_list_items (shopping_list_id, product_id, quantity, unit_price_snapshot, need_classification)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """,
            (active_list["id"], product_id, quantity, unit_price, need_response or "planned_need"),
        )

        # Recalculate list subtotal + 20% safety reserve
        cur.execute("SELECT * FROM shopping_list_items WHERE shopping_list_id = %s", (active_list["id"],))
        all_items = cur.fetchall()
        budget_summary = calculate_shopping_budget(all_items)
        cur.execute(
            """
            UPDATE shopping_lists
            SET planned_subtotal = %s, safety_reserve = %s, recommended_budget = %s
            WHERE id = %s
            """,
            (
                budget_summary["subtotal"],
                budget_summary["safety_reserve"],
                budget_summary["recommended_budget"],
                active_list["id"],
            ),
        )

    pantry_notice = (
        f" Pantry reminder: You already have {pantry_match['quantity_remaining']} {pantry_match['unit']} of {pantry_match['item_name']} recorded."
        if pantry_match
        else ""
    )
    return jsonify({
        "status": "added",
        "message": f"Added {prod['name']} to your shopping list.{pantry_notice}",
        "budget": budget_summary,
    })


@planner_bp.route("/api/list/item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_list_item(item_id: int):
    user_id = session["user_id"]
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT sli.id, sli.shopping_list_id, sl.is_locked
            FROM shopping_list_items sli
            JOIN shopping_lists sl ON sli.shopping_list_id = sl.id
            WHERE sli.id = %s AND sl.user_id = %s
            """,
            (item_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"status": "not_found", "message": "Item not found in your shopping list."}), 404
        if row.get("is_locked"):
            return jsonify({"status": "locked", "message": "This shopping list is locked."}), 409

        list_id = row["shopping_list_id"]
        cur.execute("DELETE FROM shopping_list_items WHERE id = %s", (item_id,))

        cur.execute("SELECT * FROM shopping_list_items WHERE shopping_list_id = %s", (list_id,))
        remaining_items = cur.fetchall()
        budget_summary = calculate_shopping_budget(remaining_items)

        cur.execute(
            """
            UPDATE shopping_lists
            SET planned_subtotal = %s, safety_reserve = %s, recommended_budget = %s
            WHERE id = %s
            """,
            (
                budget_summary["subtotal"],
                budget_summary["safety_reserve"],
                budget_summary["recommended_budget"],
                list_id,
            ),
        )

    return jsonify({
        "status": "deleted",
        "message": "Removed item from your shopping list.",
        "budget": budget_summary,
    })
# routes/analysis.py
from flask import Blueprint, jsonify, request
from routes.auth import login_required
from models.db import get_db_cursor
from services.ai_ingredient_service import analyze_product_ingredients

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/api/product/<int:product_id>/ingredients", methods=["GET", "POST"])
@login_required
def product_ingredient_analysis(product_id: int):
    uploaded_text = request.form.get("label_text") if request.method == "POST" else None
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT p.*, b.name AS brand_name
            FROM products p JOIN brands b ON p.brand_id = b.id
            WHERE p.id = %s
            """,
            (product_id,),
        )
        product = cur.fetchone()
        if not product:
            return jsonify({"error": "Product not found"}), 404

        cur.execute("SELECT * FROM organic_certifications WHERE product_id = %s", (product_id,))
        product["certifications"] = cur.fetchall()
        cur.execute(
            """
            SELECT i.*, pi.verification_status
            FROM product_ingredients pi JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.product_id = %s ORDER BY pi.position_order
            """,
            (product_id,),
        )
        product["ingredients"] = cur.fetchall()

    analysis = analyze_product_ingredients(product, uploaded_text)
    return jsonify({"product": product["name"], "analysis": analysis})
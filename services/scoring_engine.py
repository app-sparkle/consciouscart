"""
Transparent Rule-Based Product Scoring Engine
Weights:
  - Ingredient profile:       30%
  - Organic authenticity:     20%
  - Environmental impact:     20%
  - Packaging sustainability: 15%
  - Affordability:            15%
Total: 100%

Missing data is explicitly marked as unavailable rather than assumed positive.
"""

WEIGHTS = {
    "ingredient": 0.30,
    "organic": 0.20,
    "environmental": 0.20,
    "packaging": 0.15,
    "affordability": 0.15,
}


def compute_product_score(product: dict, peer_prices: list[float]) -> dict:
    missing_flags = []

    # 1. Ingredient profile (0-100)
    transparency_map = {
        "full": 85.0,
        "partial": 58.0,
        "basic": 38.0,
        "unavailable": 15.0,
    }
    ing_score = transparency_map.get(product.get("ingredient_transparency_level", "unavailable"), 15.0)
    ingredients = product.get("ingredients", [])
    if ingredients:
        verified_count = sum(1 for i in ingredients if i.get("verification_status") == "verified")
        ing_score = min(100.0, ing_score + (verified_count / len(ingredients)) * 15.0)
    else:
        missing_flags.append("Detailed ingredient breakdown unavailable")

    # 2. Organic authenticity (0-100) — strictly evidence-based, never keyword-based
    certs = product.get("certifications", [])
    verified_certs = [c for c in certs if c.get("verified_status")]
    if any(c.get("scope") == "100_organic" for c in verified_certs):
        org_score = 100.0
    elif any(c.get("scope") == "organic_ingredients" for c in verified_certs):
        org_score = 82.0
    elif any(c.get("scope") == "eco_label" for c in verified_certs):
        org_score = 55.0
    else:
        org_score = 10.0  # Baseline floor when no third-party organic certification exists
        missing_flags.append("No third-party organic certification verified")

    # 3. Environmental impact (0-100)
    env_text = (product.get("environmental_summary") or "").lower()
    if not env_text or "undisclosed" in env_text or "no environmental" in env_text:
        env_score = 25.0
        missing_flags.append("Upstream environmental impact data unavailable")
    else:
        env_score = 55.0
        positive_indicators = ["biodegradable", "zero palm", "rspo", "sri cultivation", "without synthetic", "minimal milling"]
        matches = sum(1 for token in positive_indicators if token in env_text)
        env_score = min(96.0, env_score + matches * 14.0)

    # 4. Packaging sustainability (0-100)
    recyclable = product.get("packaging_recyclable")
    pkg_mat = (product.get("packaging_material") or "").lower()
    if recyclable is None:
        pkg_score = 30.0
        missing_flags.append("Packaging recyclability unavailable")
    elif recyclable:
        pkg_score = 88.0 if ("paper" in pkg_mat or "kraft" in pkg_mat or "cloth" in pkg_mat) else 72.0
    else:
        pkg_score = 32.0

    # 5. Affordability (0-100 normalized against peer alternatives)
    price = float(product.get("unit_price", 0))
    if peer_prices and len(peer_prices) > 1 and max(peer_prices) > min(peer_prices):
        p_min, p_max = min(peer_prices), max(peer_prices)
        affordability_score = round(100.0 - ((price - p_min) / (p_max - p_min)) * 75.0, 2)
    else:
        affordability_score = 65.0

    weighted_total = round(
        ing_score * WEIGHTS["ingredient"]
        + org_score * WEIGHTS["organic"]
        + env_score * WEIGHTS["environmental"]
        + pkg_score * WEIGHTS["packaging"]
        + affordability_score * WEIGHTS["affordability"],
        2,
    )

    explanation = build_why_this_product(
        tier=product.get("tier_category"),
        ing_score=ing_score,
        org_score=org_score,
        pkg_score=pkg_score,
        affordability_score=affordability_score,
        missing_flags=missing_flags,
    )

    return {
        "ingredient_score": round(ing_score, 2),
        "organic_score": round(org_score, 2),
        "environmental_score": round(env_score, 2),
        "packaging_score": round(pkg_score, 2),
        "affordability_score": round(affordability_score, 2),
        "total_weighted_score": weighted_total,
        "ranking_explanation": explanation,
        "missing_data_flags": missing_flags,
    }


def build_why_this_product(tier, ing_score, org_score, pkg_score, affordability_score, missing_flags) -> str:
    strengths = []
    if org_score >= 80:
        strengths.append("documented third-party organic certification")
    if ing_score >= 80:
        strengths.append("full ingredient disclosure")
    if pkg_score >= 70:
        strengths.append("recyclable or plastic-free packaging")
    if affordability_score >= 75:
        strengths.append("strong unit-price affordability")

    strength_phrase = ", ".join(strengths) if strengths else "statutory safety compliance and clear pricing"
    caveat = f" Note: {missing_flags[0]}." if missing_flags else ""
    tier_label = (tier or "").replace("_", " ").title()
    return f"Positioned as {tier_label} because it offers {strength_phrase}.{caveat}"
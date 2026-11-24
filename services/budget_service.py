from decimal import Decimal, ROUND_HALF_UP


def calculate_shopping_budget(items: list[dict], actual_spent: float = 0.0) -> dict:
    """
    Formula:
      Subtotal = Sum(unit_price * quantity)
      Safety Reserve = Subtotal * 20%
      Recommended Shopping Budget = Subtotal + Safety Reserve
    Never automatically increases the budget when spending exceeds the plan.
    """
    subtotal = Decimal("0.00")
    for item in items:
        price = Decimal(str(item["unit_price_snapshot"]))
        qty = Decimal(str(item["quantity"]))
        subtotal += price * qty

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    safety_reserve = (subtotal * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    recommended_budget = (subtotal + safety_reserve).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    actual = Decimal(str(actual_spent)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    remaining_vs_planned = (subtotal - actual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    remaining_with_buffer = (recommended_budget - actual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    exceeded_planned = actual > subtotal and subtotal > Decimal("0.00")
    exceeded_total_buffer = actual > recommended_budget and recommended_budget > Decimal("0.00")

    warning_message = None
    if exceeded_total_buffer:
        warning_message = (
            f"Budget Exceeded: Actual spending (₹{actual}) has surpassed both your planned subtotal "
            f"(₹{subtotal}) and your 20% safety reserve ceiling (₹{recommended_budget}). "
            "Your planned budget has not been auto-increased—review non-essential items."
        )
    elif exceeded_planned:
        warning_message = (
            f"Buffer Notice: Actual spending (₹{actual}) exceeds your planned subtotal (₹{subtotal}) "
            f"and is drawing from your 20% safety buffer (₹{safety_reserve})."
        )

    return {
        "subtotal": float(subtotal),
        "safety_reserve": float(safety_reserve),
        "recommended_budget": float(recommended_budget),
        "actual_spent": float(actual),
        "remaining_vs_planned": float(remaining_vs_planned),
        "remaining_with_buffer": float(remaining_with_buffer),
        "exceeded_planned": exceeded_planned,
        "exceeded_total_buffer": exceeded_total_buffer,
        "warning_message": warning_message,
    }
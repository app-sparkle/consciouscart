import math


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def build_geofence_reminder(location_name: str, pending_count: int, recommended_budget: float, budget_exceeded: bool) -> str:
    lines = [
        f"You're near your saved shopping location ({location_name})!",
        "Before entering:",
        "- Check your shopping list.",
        "- Stick to your planned budget.",
        "- Purchase only what you need.",
        "- Make informed and responsible product choices.",
    ]
    if pending_count == 0:
        lines.append("Reminder: You currently have no planned shopping items on your active list.")
    else:
        lines.append(f"Pending planned items: {pending_count}.")
        lines.append(f"Your estimated shopping budget: ₹{recommended_budget:,.2f}.")

    if budget_exceeded:
        lines.append("Gentle spending reminder: Your current expenditure has already exceeded your planned budget.")

    lines.append("Shop Smart. Consume Responsibly.")
    return "\n".join(lines)
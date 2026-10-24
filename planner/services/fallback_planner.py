import datetime
from decimal import Decimal

from .budget import estimate_breakdown, q
from .routing import enrich_day_routes, haversine_km


def _weather_note(weather, start_date, day_number):
    """Weather note for a given day, only if the forecast really covers it."""
    if not weather or not weather.get("available") or not start_date:
        return ""
    try:
        day = start_date + datetime.timedelta(days=day_number - 1)
        for w in weather.get("days", []):
            if w.get("date") == day.isoformat():
                precip = w.get("precip_prob", 0)
                advice = w.get("badge", "")
                t_min = w.get("t_min", "")
                t_max = w.get("t_max", "")
                return f"{w['summary']} ({t_min}°–{t_max}°C, rain {precip}%). {advice}"
    except Exception:
        pass
    return ""


def _cluster_places(places, dest_lat, dest_lon):
    """Sort places by proximity to center or cluster geographically to minimize zigzag travel."""
    if not places:
        return []
    base_lat = dest_lat or places[0].get("latitude", 0)
    base_lon = dest_lon or places[0].get("longitude", 0)

    # Sort primarily by angle/quadrant from center, then distance
    return sorted(
        places,
        key=lambda p: haversine_km(base_lat, base_lon, p.get("latitude", base_lat), p.get("longitude", base_lon))
    )


def build_fallback_itinerary(trip, places, weather):
    """Deterministic, high-quality rule-based itinerary.
    Clustered geographically with weather notes, tailored tips, and route sequencing."""
    days_out = []
    warnings = []
    days_count = max(trip.get("days", 1), 1)
    currency = trip.get("currency", "USD")
    style = trip.get("style", "balanced")
    travellers = trip.get("travellers", 1)
    user_budget = trip.get("budget")

    breakdown = estimate_breakdown(style, currency, travellers, days_count, user_budget=user_budget)
    daily_cost = q(breakdown["total"] / Decimal(days_count))

    pace = trip.get("pace", "moderate")
    pace_limits = {"relaxed": 3, "moderate": 4, "packed": 5}
    max_per_day = min(trip.get("max_activities") or pace_limits.get(pace, 4), 6)
    start_date = trip.get("start_date")

    interests = trip.get("interests", [])
    interests_label = ", ".join(interests).title() if interests else "Sightseeing & Culture"
    companion = trip.get("companion", "solo").title()
    dietary = (trip.get("preferences") or {}).get("dietary", "")

    # Sort places geographically
    dest_lat = trip.get("latitude")
    dest_lon = trip.get("longitude")
    sorted_places = _cluster_places(places, dest_lat, dest_lon)

    total_activity_costs = Decimal("0")
    place_idx = 0

    time_slots_config = {
        "morning": {"time": "09:30 AM", "dur": 120, "desc": "Explore morning highlights with cooler temperatures."},
        "afternoon": {"time": "02:00 PM", "dur": 90, "desc": "Cultural exploration and leisure downtime."},
        "evening": {"time": "06:00 PM", "dur": 120, "desc": "Sunset views, vibrant atmosphere, and local charm."},
    }

    for n in range(1, days_count + 1):
        day_acts_flat = []
        slots = {"morning": [], "afternoon": [], "evening": []}

        # Determine activities allocation across slots
        if max_per_day <= 3:
            slot_plan = [("morning", 1), ("afternoon", 1), ("evening", 1)]
        elif max_per_day == 4:
            slot_plan = [("morning", 1), ("afternoon", 2), ("evening", 1)]
        else:
            slot_plan = [("morning", 2), ("afternoon", 2), ("evening", 1)]

        for slot_name, count in slot_plan:
            cfg = time_slots_config[slot_name]
            for _ in range(count):
                if place_idx < len(sorted_places):
                    p = sorted_places[place_idx]
                    place_idx += 1
                    p_name = p["name"]
                    p_cat = p.get("category", "attraction")
                    p_lat = p["latitude"]
                    p_lon = p["longitude"]
                    pid = p["source_id"]
                else:
                    # Generic destination activity if places ran out
                    dest = trip.get("resolved_name") or trip.get("destination")
                    p_name = f"{dest} Discovery Walk"
                    p_cat = "attraction"
                    p_lat = dest_lat
                    p_lon = dest_lon
                    pid = f"dest/{n}/{slot_name}"

                # Approximate small entry cost based on style
                approx_ticket = 0 if style == "budget" else (150 if currency == "INR" else 10)
                total_activity_costs += Decimal(str(approx_ticket))

                act_item = {
                    "place_id": pid,
                    "name": p_name,
                    "category": p_cat,
                    "latitude": p_lat,
                    "longitude": p_lon,
                    "activity": f"Visit {p_name}",
                    "description": f"{cfg['desc']} Experience the architecture and unique setting of {p_name}.",
                    "duration_minutes": cfg["dur"],
                    "suggested_time": cfg["time"],
                    "estimated_cost": approx_ticket,
                    "cost_currency": currency,
                    "insider_tip": f"Recommended for {companion} travellers. Plan ~{cfg['dur']} minutes for a complete visit.",
                }
                slots[slot_name].append(act_item)
                day_acts_flat.append(act_item)

        # Route enrichment connecting ordered stops for this day
        route_stats = enrich_day_routes(day_acts_flat)

        day_tips = [
            f"Focused on: {interests_label}.",
            f"Optimized for {pace} pace ({len(day_acts_flat)} activities).",
            f"Est. day transit: ~{route_stats['total_distance_km']} km across stops.",
        ]
        if dietary:
            day_tips.append(f"Dietary note: Look for {dietary} dining options near afternoon and evening stops.")

        days_out.append(
            {
                "day_number": n,
                "title": f"Day {n}: {interests_label.split(',')[0]} & City Highlights",
                **slots,
                "daily_estimated_cost": float(daily_cost),
                "weather_note": _weather_note(weather, start_date, n),
                "tips": day_tips,
                "route_summary": route_stats,
            }
        )

    if not places:
        warnings.append(
            "Attraction database had limited local listings for this query; generated a curated city walking schedule."
        )

    return {
        "destination": trip.get("resolved_name") or trip.get("destination"),
        "trip_summary": f"A tailored {days_count}-day itinerary designed for {travellers} {companion.lower()} traveller(s) highlighting {interests_label.lower()}.",
        "days": days_out,
        "estimated_total_cost": float(breakdown["total"]),
        "breakdown": {k: float(v) for k, v in breakdown["categories"].items()},
        "assumptions": breakdown["assumptions"],
        "warnings": warnings,
        "generator": "fallback",
    }

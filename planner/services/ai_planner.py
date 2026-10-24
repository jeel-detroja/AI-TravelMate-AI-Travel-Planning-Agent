import json
import logging
from decimal import Decimal

from django.conf import settings

from .budget import estimate_breakdown, q
from .fallback_planner import _weather_note, build_fallback_itinerary
from .routing import enrich_day_routes, haversine_km

log = logging.getLogger("planner")

SYSTEM_INSTRUCTION = (
    "You are an elite, world-class travel planner and destination concierge. "
    "Your objective is to craft an exceptional, realistic, highly tailored day-by-day travel itinerary "
    "matching the user's destination, budget, dates, group size, companion type, travel style, pace, "
    "selected interests, dietary preferences, accessibility needs, and real weather forecast.\n\n"
    "CRITICAL RULES:\n"
    "1. Strict JSON output only. No markdown formatting, no code fences, no introductory or trailing text.\n"
    "2. Group each day's activities in the same neighborhood or geographic corridor to minimize travel time.\n"
    "3. Respect the user's travel style (budget/balanced/premium) and pace (relaxed: 2-3 activities/day; moderate: 3-4; packed: 4-5).\n"
    "4. For meals and dining tips, strictly honor the user's dietary preferences (e.g. Vegetarian, Vegan, Halal, Gluten-Free).\n"
    "5. Adapt activities to the weather forecast (e.g. schedule indoor museums/art galleries/markets during rain; outdoor viewpoints during clear skies).\n"
    "6. Prioritize verified places when provided; you may supplement with renowned authentic landmarks, viewpoints, and cultural experiences for the destination.\n"
    "7. Include practical, high-value insider tips for every activity (best photo angles, avoiding queues, ticket advice, cultural etiquette).\n"
    "8. Assign realistic entry or activity costs in the user's specified currency.\n"
    "9. Produce exactly the requested number of days with day_number 1 to N."
)

JSON_SCHEMA_TEMPLATE = {
    "trip_summary": "1-2 sentence inspiring overview of the customized journey.",
    "days": [
        {
            "day_number": 1,
            "title": "Inspiring Day Theme (e.g., 'Royal Palaces & Historic Bazaars')",
            "morning": [
                {
                    "place_id": "node/123",
                    "name": "Attraction Name",
                    "category": "historic",
                    "activity": "Vivid Title (e.g., 'Explore the Mirror Palace of Amber Fort')",
                    "description": "2-3 sentences explaining what to experience and historical significance.",
                    "suggested_time": "09:30 AM - 11:30 AM",
                    "duration_minutes": 120,
                    "estimated_cost": 250,
                    "latitude": 26.985,
                    "longitude": 75.851,
                    "insider_tip": "Arrive before 10 AM to avoid crowds and get the best sunlight for photography."
                }
            ],
            "afternoon": [],
            "evening": [],
            "dining_recommendations": [
                {
                    "meal": "Lunch",
                    "name": "Restaurant / Cafe Name",
                    "cuisine": "Regional Cuisine",
                    "dietary_notes": "Offers excellent vegetarian options.",
                    "price_tier": "Moderate"
                }
            ],
            "tips": [
                "Practical daily transit or packing advice."
            ]
        }
    ],
    "packing_and_safety_tips": [
        "Key local tip or cultural guideline."
    ],
    "warnings": []
}


def _build_prompt(trip, places, weather):
    place_list = [
        {
            "place_id": p.get("source_id"),
            "name": p.get("name"),
            "category": p.get("category"),
            "lat": p.get("latitude"),
            "lon": p.get("longitude"),
        }
        for p in places[:35]
    ]

    weather_summary = []
    if weather and weather.get("available"):
        for wd in weather.get("days", []):
            weather_summary.append({
                "date": wd.get("date"),
                "sky": wd.get("summary"),
                "high_c": wd.get("t_max"),
                "low_c": wd.get("t_min"),
                "rain_chance_pct": wd.get("precip_prob", 0),
                "advice": wd.get("badge", ""),
            })

    user_payload = {
        "destination": trip.get("resolved_name") or trip.get("destination"),
        "destination_center": {
            "latitude": trip.get("latitude"),
            "longitude": trip.get("longitude"),
        },
        "days_count": trip.get("days"),
        "start_date": str(trip.get("start_date")),
        "travellers_count": trip.get("travellers"),
        "companion_type": trip.get("companion"),
        "total_budget": float(trip.get("budget", 0)) if trip.get("budget") else None,
        "currency": trip.get("currency", "USD"),
        "travel_style": trip.get("style", "balanced"),
        "pace": trip.get("pace", "moderate"),
        "selected_interests": trip.get("interests", []),
        "dietary_preferences": (trip.get("preferences") or {}).get("dietary") or "None specified",
        "accessibility_needs": (trip.get("preferences") or {}).get("accessibility") or "None specified",
        "max_activities_per_day": trip.get("max_activities") or 4,
        "weather_forecast": weather_summary,
        "verified_places_pool": place_list,
    }

    return (
        f"Generate a customized day-by-day travel plan based on these user trip details:\n"
        f"{json.dumps(user_payload, indent=2)}\n\n"
        f"Return ONLY valid JSON strictly following this schema structure:\n"
        f"{json.dumps(JSON_SCHEMA_TEMPLATE, indent=2)}"
    )


def _call_gemini(prompt):
    cfg = settings.TRAVELMATE
    from google import genai  # requires `google-genai`

    client = genai.Client(api_key=cfg["GEMINI_API_KEY"])
    models_to_try = [
        cfg.get("GEMINI_MODEL") or "gemini-2.5-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3.5-flash-lite",
    ]
    # Remove duplicates preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    last_error = None
    for model_name in models_to_try:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                    "temperature": 0.3,
                },
            )
            if resp and resp.text:
                return resp.text
        except Exception as exc:
            last_error = exc
            log.warning("Gemini model %s failed: %s; trying next model.", model_name, exc)
            continue

    raise last_error or RuntimeError("Gemini API returned empty response across all models.")


def _clean_coordinates(lat, lon, dest_lat, dest_lon):
    try:
        lat = float(lat)
        lon = float(lon)
        if dest_lat is not None and dest_lon is not None:
            normal_dist = haversine_km(lat, lon, dest_lat, dest_lon)
            swapped_dist = haversine_km(lon, lat, dest_lat, dest_lon)
            if swapped_dist < normal_dist and swapped_dist <= 35.0:
                return lon, lat
            if normal_dist > 45.0:
                return dest_lat, dest_lon
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    except (TypeError, ValueError):
        pass
    return dest_lat, dest_lon


def _validate_and_normalize(raw, trip, places, weather=None):
    """Validate AI response, sanitize data, enrich routes, and compute budgets."""
    try:
        # Strip potential markdown fences if present
        clean_raw = raw.strip()
        if clean_raw.startswith("```json"):
            clean_raw = clean_raw[7:]
        if clean_raw.startswith("```"):
            clean_raw = clean_raw[3:]
        if clean_raw.endswith("```"):
            clean_raw = clean_raw[:-3]
        parsed = json.loads(clean_raw.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"AI returned malformed JSON: {exc}")

    if not isinstance(parsed, dict):
        raise ValueError("AI returned an unexpected root structure.")

    ai_days = parsed.get("days")
    if not isinstance(ai_days, list) or not ai_days:
        raise ValueError("AI returned no days.")

    req_days = trip.get("days", len(ai_days))
    if len(ai_days) != req_days:
        raise ValueError(f"AI returned {len(ai_days)} days instead of requested {req_days}.")

    place_by_id = {p["source_id"]: p for p in places if "source_id" in p}
    dest_lat = trip.get("latitude")
    dest_lon = trip.get("longitude")
    user_budget = trip.get("budget")
    currency = trip.get("currency", "USD")

    breakdown = estimate_breakdown(
        trip["style"], currency, trip["travellers"], req_days, user_budget=user_budget
    )
    daily_cost = q(breakdown["total"] / Decimal(max(req_days, 1)))

    clean_days = []
    seen_activities = set()
    total_activity_ticket_costs = Decimal("0")

    for n, day in enumerate(ai_days, start=1):
        if not isinstance(day, dict):
            raise ValueError(f"Day {n} is malformed.")

        day_acts_flat = []
        clean_day = {
            "day_number": n,
            "title": str(day.get("title") or f"Day {n}: City Discovery")[:120],
            "morning": [],
            "afternoon": [],
            "evening": [],
            "dining_recommendations": (day.get("dining_recommendations") or [])[:3],
            "daily_estimated_cost": float(daily_cost),
            "weather_note": _weather_note(weather, trip.get("start_date"), n),
            "tips": [str(t)[:250] for t in (day.get("tips") or [])][:5],
        }

        for slot in ("morning", "afternoon", "evening"):
            slot_items = day.get(slot) or []
            if not isinstance(slot_items, list):
                continue

            for item in slot_items[:4]:
                if not isinstance(item, dict):
                    continue

                name = str(item.get("name") or item.get("activity") or "Attraction")[:120].strip()
                name_key = name.lower()
                if name_key in seen_activities:
                    continue  # avoid repeating the same place across the trip
                seen_activities.add(name_key)

                pid = item.get("place_id") or f"poi/{n}/{slot}/{len(clean_day[slot])}"
                matched_place = place_by_id.get(pid)

                # Prioritize verified coordinates, otherwise AI coordinates, otherwise destination center
                raw_lat = matched_place["latitude"] if matched_place else item.get("latitude")
                raw_lon = matched_place["longitude"] if matched_place else item.get("longitude")
                lat, lon = _clean_coordinates(raw_lat, raw_lon, dest_lat, dest_lon)

                category = matched_place["category"] if matched_place else str(item.get("category") or "attraction")[:50]

                try:
                    dur = int(item.get("duration_minutes", 90))
                except (TypeError, ValueError):
                    dur = 90
                dur = max(20, min(dur, 360))

                try:
                    cost_val = float(item.get("estimated_cost", 0))
                    cost_val = max(0.0, min(cost_val, 100000.0))
                except (TypeError, ValueError):
                    cost_val = 0.0

                total_activity_ticket_costs += Decimal(str(cost_val))

                act_entry = {
                    "place_id": pid,
                    "name": name,
                    "category": category,
                    "latitude": lat,
                    "longitude": lon,
                    "activity": str(item.get("activity") or f"Visit {name}")[:200],
                    "description": str(item.get("description") or f"Experience {name} and its scenic surroundings.")[:400],
                    "suggested_time": str(item.get("suggested_time") or "")[:50],
                    "duration_minutes": dur,
                    "estimated_cost": cost_val,
                    "cost_currency": currency,
                    "insider_tip": str(item.get("insider_tip") or "Plan ahead and check local opening times.")[:250],
                }

                clean_day[slot].append(act_entry)
                day_acts_flat.append(act_entry)

        # Enrich with route distances and travel times
        route_stats = enrich_day_routes(day_acts_flat)
        clean_day["route_summary"] = route_stats
        clean_days.append(clean_day)

    warnings = [str(w)[:200] for w in (parsed.get("warnings") or [])[:5]]

    return {
        "destination": trip.get("resolved_name") or trip.get("destination"),
        "trip_summary": str(parsed.get("trip_summary") or f"Curated itinerary for {trip.get('destination')}")[:400],
        "days": clean_days,
        "estimated_total_cost": float(breakdown["total"]),
        "breakdown": {k: float(v) for k, v in breakdown["categories"].items()},
        "assumptions": breakdown["assumptions"],
        "activity_ticket_costs": float(total_activity_ticket_costs),
        "packing_and_safety_tips": (parsed.get("packing_and_safety_tips") or [])[:5],
        "warnings": warnings,
        "generator": "gemini",
    }


def generate_itinerary(trip, places, weather):
    """Generate itinerary via Gemini when configured, with seamless fallback."""
    cfg = settings.TRAVELMATE
    if cfg["AI_PROVIDER"] == "gemini" and cfg["GEMINI_API_KEY"]:
        try:
            prompt = _build_prompt(trip, places, weather)
            raw = _call_gemini(prompt)
            result = _validate_and_normalize(raw, trip, places, weather)
            log.info("Itinerary generated via Gemini for %s", trip["destination"])
            return result
        except ImportError:
            log.warning("google-genai not installed; using fallback.")
        except Exception as exc:
            log.warning("Gemini generation failed (%s: %s); using fallback.", exc.__class__.__name__, exc)

    return build_fallback_itinerary(trip, places, weather)

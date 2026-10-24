from math import asin, cos, radians, sin, sqrt
import urllib.parse


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line (great-circle) distance in km."""
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        r = 6371.0
        dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return round(2 * r * asin(sqrt(a)), 2)
    except (TypeError, ValueError):
        return 0.0


def estimate_transit(dist_km):
    """Estimate travel mode and duration based on geographic distance."""
    if dist_km <= 0.05:
        return {
            "mode": "Adjacent",
            "duration_minutes": 2,
            "icon": "bi-geo-alt",
            "badge": "Same neighborhood (<100m)",
        }
    elif dist_km <= 1.5:
        mins = max(4, round(dist_km * 13))
        return {
            "mode": "Walking",
            "duration_minutes": mins,
            "icon": "bi-person-walking",
            "badge": f"{dist_km:.1f} km · ~{mins} min walk",
        }
    elif dist_km <= 6.0:
        mins = max(10, round(dist_km * 4 + 7))
        return {
            "mode": "Transit / Cab",
            "duration_minutes": mins,
            "icon": "bi-taxi-front",
            "badge": f"{dist_km:.1f} km · ~{mins} min drive/auto",
        }
    else:
        mins = max(20, round(dist_km * 3 + 12))
        return {
            "mode": "Metro / Drive",
            "duration_minutes": mins,
            "icon": "bi-car-front",
            "badge": f"{dist_km:.1f} km · ~{mins} min transit/drive",
        }


def external_nav_url(lat, lon, label=None):
    """Direct map view URL."""
    try:
        lat, lon = float(lat), float(lon)
        return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"
    except (TypeError, ValueError):
        return "#"


def route_directions_url(lat1, lon1, lat2, lon2, origin_name="", dest_name=""):
    """Google Maps directions link between two stops."""
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        base = "https://www.google.com/maps/dir/?api=1"
        origin = f"{lat1},{lon1}"
        destination = f"{lat2},{lon2}"
        params = {
            "origin": origin,
            "destination": destination,
            "travelmode": "transit" if haversine_km(lat1, lon1, lat2, lon2) > 1.5 else "walking",
        }
        return f"{base}&{urllib.parse.urlencode(params)}"
    except (TypeError, ValueError):
        return "#"


def enrich_day_routes(activities):
    """Connect ordered activities within a day with distance, transit mode,
    duration, and step-by-step navigation."""
    total_km = 0.0
    total_transit_mins = 0

    valid_acts = [
        a for a in activities
        if a.get("latitude") is not None and a.get("longitude") is not None
    ]

    for i in range(len(valid_acts) - 1):
        curr_act = valid_acts[i]
        next_act = valid_acts[i + 1]
        dist = haversine_km(
            curr_act["latitude"], curr_act["longitude"],
            next_act["latitude"], next_act["longitude"]
        )
        transit = estimate_transit(dist)
        nav_url = route_directions_url(
            curr_act["latitude"], curr_act["longitude"],
            next_act["latitude"], next_act["longitude"],
            curr_act.get("name", ""), next_act.get("name", "")
        )

        curr_act["route_to_next"] = {
            "distance_km": dist,
            "duration_minutes": transit["duration_minutes"],
            "mode": transit["mode"],
            "icon": transit["icon"],
            "badge": transit["badge"],
            "nav_url": nav_url,
            "to_name": next_act.get("name", "Next stop"),
        }
        total_km += dist
        total_transit_mins += transit["duration_minutes"]

    return {
        "total_distance_km": round(total_km, 1),
        "total_transit_minutes": total_transit_mins,
    }

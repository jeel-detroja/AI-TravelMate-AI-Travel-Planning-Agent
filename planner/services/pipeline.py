import logging

from .ai_planner import generate_itinerary
from .geocoding import geocode
from .http import ServiceError
from .places import find_places
from .weather import get_weather

log = logging.getLogger("planner")


def generate_for_trip(trip):
    """Run the verified-data + AI planner pipeline for a Trip instance.
    Returns (itinerary_dict | None, weather_dict, warnings_list)."""
    warnings = []
    geo = None
    try:
        geo = geocode(trip.destination)
    except ServiceError:
        warnings.append("Geocoding service was unavailable. Please try again shortly.")

    if not geo:
        if not warnings:
            warnings.append(
                f"Could not find '{trip.destination}'. Check the spelling or try a nearby city."
            )
        return None, {"available": False, "days": []}, warnings

    trip.resolved_name = geo["display_name"]
    trip.latitude = geo["latitude"]
    trip.longitude = geo["longitude"]
    trip.save(update_fields=["resolved_name", "latitude", "longitude"])

    try:
        places = find_places(trip.latitude, trip.longitude, trip.interests)
    except ServiceError:
        places = []
        warnings.append("Attraction database was temporarily unavailable; using AI landmark synthesis.")

    weather = get_weather(trip.latitude, trip.longitude, trip.start_date, trip.end_date)
    if not weather.get("available"):
        warnings.append(
            "Live weather forecast is unavailable for dates beyond ~16 days."
        )

    trip_payload = {
        "destination": trip.destination,
        "resolved_name": trip.resolved_name,
        "latitude": trip.latitude,
        "longitude": trip.longitude,
        "start_date": trip.start_date,
        "days": trip.duration_days,
        "budget": trip.budget,
        "travellers": trip.travellers,
        "currency": trip.currency,
        "interests": trip.interests,
        "style": trip.travel_style,
        "pace": trip.pace,
        "companion": trip.companion,
        "preferences": trip.preferences or {},
        "max_activities": (trip.preferences or {}).get("max_activities"),
    }
    itinerary = generate_itinerary(trip_payload, places, weather)
    itinerary["warnings"] = list(dict.fromkeys(warnings + itinerary.get("warnings", [])))
    return itinerary, weather, itinerary["warnings"]

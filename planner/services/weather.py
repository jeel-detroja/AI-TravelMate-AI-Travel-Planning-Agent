from django.conf import settings

from .cache import cached
from .http import ServiceError, get_json

WMO = {
    0: {"summary": "Clear sky", "icon": "bi-sun-fill", "badge": "Great for outdoor sights"},
    1: {"summary": "Mainly clear", "icon": "bi-sun", "badge": "Sunny & pleasant"},
    2: {"summary": "Partly cloudy", "icon": "bi-cloud-sun", "badge": "Comfortable for walking"},
    3: {"summary": "Overcast", "icon": "bi-clouds", "badge": "Mild & overcast"},
    45: {"summary": "Fog", "icon": "bi-cloud-fog", "badge": "Low visibility early morning"},
    48: {"summary": "Rime fog", "icon": "bi-cloud-fog2", "badge": "Cool & misty"},
    51: {"summary": "Light drizzle", "icon": "bi-cloud-drizzle", "badge": "Carry a light umbrella"},
    53: {"summary": "Drizzle", "icon": "bi-cloud-drizzle-fill", "badge": "Intermittent drizzle"},
    55: {"summary": "Heavy drizzle", "icon": "bi-cloud-rain", "badge": "Rain gear recommended"},
    61: {"summary": "Light rain", "icon": "bi-cloud-rain", "badge": "Light rain expected"},
    63: {"summary": "Rain", "icon": "bi-cloud-rain-heavy", "badge": "Rain likely · Favor indoor venues"},
    65: {"summary": "Heavy rain", "icon": "bi-cloud-rain-heavy-fill", "badge": "Heavy rain · Best for museums/indoor"},
    71: {"summary": "Light snow", "icon": "bi-snow", "badge": "Light snow · Dress warmly"},
    73: {"summary": "Snow", "icon": "bi-snow2", "badge": "Snowing · Winter gear required"},
    75: {"summary": "Heavy snow", "icon": "bi-snow3", "badge": "Heavy snow · Plan indoor activities"},
    80: {"summary": "Rain showers", "icon": "bi-cloud-rain", "badge": "Passing showers"},
    81: {"summary": "Rain showers", "icon": "bi-cloud-rain-heavy", "badge": "Scattered rain showers"},
    82: {"summary": "Violent rain showers", "icon": "bi-cloud-lightning-rain", "badge": "Intense rain · Stay sheltered"},
    95: {"summary": "Thunderstorm", "icon": "bi-cloud-lightning", "badge": "Thunderstorms · Avoid open peaks"},
    96: {"summary": "Thunderstorm with hail", "icon": "bi-cloud-lightning-rain-fill", "badge": "Severe storm alert"},
    99: {"summary": "Thunderstorm with hail", "icon": "bi-cloud-lightning-rain-fill", "badge": "Severe storm alert"},
}


def _at(seq, i):
    seq = seq or []
    return seq[i] if i < len(seq) else None


def get_weather(lat, lon, start_date, end_date):
    """Daily forecast from Open-Meteo, or {"available": False}."""
    cfg = settings.TRAVELMATE

    def _fetch():
        data = get_json(
            cfg["OPEN_METEO_URL"],
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max",
                "timezone": "auto",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        daily = data.get("daily") or {}
        dates = daily.get("time") or []
        if not dates:
            return {"available": False, "days": []}

        days = []
        for i, d in enumerate(dates):
            code = _at(daily.get("weather_code"), i)
            meta = WMO.get(code, {"summary": "Unknown", "icon": "bi-cloud-sun", "badge": "Check local forecast"})
            days.append(
                {
                    "date": d,
                    "code": code,
                    "summary": meta["summary"],
                    "icon": meta["icon"],
                    "badge": meta["badge"],
                    "t_max": _at(daily.get("temperature_2m_max"), i),
                    "t_min": _at(daily.get("temperature_2m_min"), i),
                    "precip_prob": _at(daily.get("precipitation_probability_max"), i) or 0,
                }
            )
        return {
            "available": True,
            "days": days,
            "attribution": "Weather data by Open-Meteo.com",
        }

    try:
        result = cached(
            "weather",
            cfg["CACHE_TTL_WEATHER"],
            _fetch,
            round(lat, 2),
            round(lon, 2),
            start_date,
            end_date,
        )
        return result or {"available": False, "days": []}
    except ServiceError:
        return {"available": False, "days": [], "error": "Weather unavailable."}

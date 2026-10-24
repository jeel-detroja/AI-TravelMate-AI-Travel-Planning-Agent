import time

from django.conf import settings

from .cache import cached
from .http import get_json

_last_call = [0.0]


def _respect_rate_limit():
    # Nominatim usage policy: max 1 request/second.
    elapsed = time.monotonic() - _last_call[0]
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_call[0] = time.monotonic()


def geocode(destination):
    """Resolve a destination string to coordinates via Nominatim.
    Returns a dict, or None if nothing was found. Raises ServiceError on failure."""
    cfg = settings.TRAVELMATE
    destination = (destination or "").strip()
    if not destination:
        return None

    def _fetch():
        _respect_rate_limit()
        results = get_json(
            f"{cfg['NOMINATIM_BASE_URL']}/search",
            params={"q": destination, "format": "jsonv2", "limit": 1, "addressdetails": 1},
        )
        if not results:
            return None
        r = results[0]
        return {
            "name": destination,
            "display_name": r.get("display_name", destination),
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"]),
            "source": "nominatim",
        }

    return cached("geocode", cfg["CACHE_TTL_GEOCODE"], _fetch, destination.lower())

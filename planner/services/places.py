import logging

from django.conf import settings

from ..constants import DEFAULT_OSM_TAGS, INTEREST_OSM_TAGS
from .cache import cached
from .http import ServiceError, get_json

log = logging.getLogger("planner")
_CATEGORY_KEYS = ("tourism", "historic", "leisure", "amenity", "natural", "shop", "building")


def _build_query(lat, lon, interests, radius_m=7000, limit=40):
    """Build an efficient Overpass query prioritizing user interests."""
    tags = []
    for interest in interests:
        tags.extend(INTEREST_OSM_TAGS.get(interest, []))
    if not tags:
        tags = list(DEFAULT_OSM_TAGS)
    else:
        tags = list(DEFAULT_OSM_TAGS[:2]) + tags

    deduped_tags = list(dict.fromkeys(tags))[:6]
    blocks = "".join(f"nwr{t}(around:{radius_m},{lat},{lon});" for t in deduped_tags)
    return f"[out:json][timeout:10];({blocks});out center {limit};"


def _category_of(tags):
    for key in _CATEGORY_KEYS:
        val = tags.get(key)
        if val and val != "yes":
            return f"{key}:{val}"
        elif val:
            return key
    return "attraction"


def find_places(lat, lon, interests, limit=35):
    """Query Overpass for verified named POIs near coordinates.
    Uses fast 10s per-mirror timeout to never block user requests."""
    cfg = settings.TRAVELMATE

    def _fetch():
        query = _build_query(lat, lon, interests, radius_m=7500, limit=limit + 20)
        urls = [
            "https://overpass.private.coffee/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            cfg["OVERPASS_URL"],
        ]
        payload = None
        for u in urls:
            try:
                payload = get_json(u, method="POST", data={"data": query}, retries=0, timeout=10)
                if payload and "elements" in payload and payload["elements"]:
                    break
            except ServiceError as exc:
                log.info("Overpass mirror %s unreachable: %s; trying next.", u, exc)
                continue

        if not payload or not isinstance(payload, dict):
            log.info("All Overpass endpoints unavailable or empty; continuing with AI synthesis.")
            return []

        out = []
        seen_ids = set()
        seen_names = set()

        for el in payload.get("elements", []):
            if el.get("type") == "node":
                plat, plon = el.get("lat"), el.get("lon")
            else:
                center = el.get("center") or {}
                plat, plon = center.get("lat"), center.get("lon")

            if plat is None or plon is None:
                continue

            tags = el.get("tags", {})
            name = (tags.get("name") or "").strip()
            if not name or len(name) < 2:
                continue

            clean_name_key = name.lower().split(" - ")[0].split(" (")[0].strip()
            if clean_name_key in seen_names:
                continue

            source_id = f"{el['type']}/{el['id']}"
            if source_id in seen_ids:
                continue

            seen_ids.add(source_id)
            seen_names.add(clean_name_key)

            out.append(
                {
                    "name": name,
                    "category": _category_of(tags),
                    "latitude": float(plat),
                    "longitude": float(plon),
                    "source": "openstreetmap",
                    "source_id": source_id,
                    "attribution": "© OpenStreetMap contributors",
                }
            )
            if len(out) >= limit:
                break

        return out

    try:
        return (
            cached(
                "places",
                cfg["CACHE_TTL_PLACES"],
                _fetch,
                round(lat, 3),
                round(lon, 3),
                ",".join(sorted(interests)),
                limit,
            )
            or []
        )
    except Exception as exc:
        log.warning("find_places error: %s", exc)
        return []

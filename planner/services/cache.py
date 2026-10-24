import hashlib

from django.core.cache import cache


def make_key(prefix, *parts):
    raw = "|".join(str(p) for p in parts)
    return f"{prefix}:" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def cached(prefix, ttl, producer, *parts):
    """Return the cached value for the key, else compute via producer() and store it.
    None results are not cached."""
    key = make_key(prefix, *parts)
    hit = cache.get(key)
    if hit is not None:
        return hit
    value = producer()
    if value is not None:
        cache.set(key, value, ttl)
    return value

import hashlib
import json

from django.core.cache import cache


def stable_hash(*parts) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def cache_get_or_set(key: str, builder, ttl: int):
    cached = cache.get(key)
    if cached is not None:
        return cached, True
    value = builder()
    cache.set(key, value, ttl)
    return value, False


def invalidate_profile(user_id):
    cache.delete(f'profile:{user_id}')


def invalidate_domains():
    cache.delete('domains:all')

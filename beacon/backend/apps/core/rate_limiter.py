import time

from django.core.cache import cache


SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now .. '-' .. math.random(1000000))
    redis.call('EXPIRE', key, window)
    return {1, limit - count - 1}
end
return {0, 0}
"""


def allow_request(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    client = cache.client.get_client(write=True)
    now = int(time.time())
    allowed, remaining = client.eval(
        SLIDING_WINDOW_LUA,
        1,
        key,
        int(window_seconds),
        int(limit),
        now,
    )
    return bool(allowed), int(remaining)

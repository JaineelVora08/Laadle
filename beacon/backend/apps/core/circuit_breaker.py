import time

from django.core.cache import cache


class CircuitOpen(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, reset_after: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_after = reset_after

    @property
    def key(self):
        return f'circuit:{self.name}'

    def call(self, fn, fallback=None):
        state = cache.get(self.key) or {'failures': 0, 'opened_at': None}
        if state.get('opened_at'):
            elapsed = time.time() - state['opened_at']
            if elapsed < self.reset_after:
                if fallback is not None:
                    return fallback()
                raise CircuitOpen(self.name)
            state = {'failures': 0, 'opened_at': None}

        try:
            result = fn()
        except Exception:
            failures = int(state.get('failures', 0)) + 1
            opened_at = time.time() if failures >= self.failure_threshold else None
            cache.set(self.key, {'failures': failures, 'opened_at': opened_at}, self.reset_after)
            if fallback is not None and opened_at:
                return fallback()
            raise

        cache.delete(self.key)
        return result

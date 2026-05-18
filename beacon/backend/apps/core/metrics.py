from prometheus_client import Counter, Gauge, Histogram

QUERY_SUBMITTED = Counter('beacon_queries_total', 'Queries submitted', ['domain'])
LLM_DURATION = Histogram(
    'beacon_llm_seconds',
    'LLM call duration',
    ['operation'],
    buckets=[0.5, 1, 2, 5, 10, 30],
)
LLM_TOKENS = Counter('beacon_llm_tokens_total', 'LLM tokens used', ['direction'])
CACHE_HIT = Counter('beacon_cache_hits', 'Cache hits', ['layer', 'type'])
ACTIVE_QUERIES = Gauge('beacon_active_queries', 'Pending queries')

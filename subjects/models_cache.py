from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT


# Define the LBD probability cache prefix
CACHE_LBD_PROBABILITY_PREFIX = 'lbd_probability'


# Get the time-to-live (TTL) for the cache
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

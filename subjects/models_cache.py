from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT


class BaseCachedModel(object):
    """Base class for the cached models"""

    # Define the LBD probability cache prefix
    CACHE_LBD_PROBABILITY_PREFIX = 'lbd_probability'

    # Get the time-to-live (TTL) for the cache
    CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

    def __init__(self, instance):
        self.instance = instance

    def get_lbd_probability_cache_key(self):
        """Gets the LBD probability cache key"""
        return None

    def get_cached_lbd_probability(self):
        """Gets the cached LBD probability"""
        return cache.get(self.get_lbd_probability_cache_key())

    def set_cached_lbd_probability(self, lbd_probability):
        """Sets the cached LBD probability"""
        cache.set(self.get_lbd_probability_cache_key(), lbd_probability, timeout=self.CACHE_TTL)


class SubjectCache(BaseCachedModel):
    """Class implementing cached subject data"""

    def get_lbd_probability_cache_key(self):
        return f'{self.CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.instance.code}'


class ExaminationSessionCache(BaseCachedModel):
    """Class implementing cached examination session data"""

    def get_lbd_probability_cache_key(self):
        return f'{self.CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.instance.subject.code}_session_{self.instance.id}'

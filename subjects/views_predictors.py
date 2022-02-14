from django.conf import settings
from predictor import predict_lbd_probability
from predictor.processors import process_features
from .models import ExaminationSession
from .models_cache import SubjectCache, ExaminationSessionCache


class BaseLBDPredictor(object):
    """Base class for LBD predictors"""

    # Define the predictor model identifier
    predictor = getattr(settings, 'PREDICTOR_CONFIGURATION')['model_identifier']

    @classmethod
    def predict_lbd_probability(cls, user, instance):
        """
        Predicts the LBD probability for a model instance.

        :param user: logged-in user
        :type user: User instance
        :param instance: model instance
        :param instance: object
        :return: predicted LBD probability
        :rtype: float
        """
        return None


class SubjectLBDPredictor(BaseLBDPredictor):
    """Class implementing the LBD predictor for subjects"""

    # Define the model cache object
    model_cache = SubjectCache

    @classmethod
    def predict_lbd_probability(cls, user, instance):
        """Predicts the LBD probability for a subject instance"""

        # Prepare the model cache instance
        cache_instance = cls.model_cache(instance)

        # Get the examination sessions of a subject (order from newest to oldest)
        sessions = ExaminationSession.get_sessions(subject=instance, order_by=('-session_number', ))

        # Get the latest examination session
        latest_session = sessions.first()
        if not latest_session:
            return None

        # Get the LBD probability for the last examination session with data
        lbd_probability = ExaminationSessionLBDPredictor.predict_lbd_probability(user, latest_session)

        # Cache the predicted LBD probability (if not None)
        if lbd_probability is not None:
            cache_instance.set_cached_lbd_probability(lbd_probability)

        # Predict the LBD probability
        return lbd_probability


class ExaminationSessionLBDPredictor(BaseLBDPredictor):
    """Class implementing the LBD predictor for examination sessions"""

    # Define the model cache object
    model_cache = ExaminationSessionCache

    @classmethod
    def predict_lbd_probability(cls, user, instance):
        """Predicts the LBD probability for an examination session instance"""

        # Prepare the model cache instance
        cache_instance = cls.model_cache(instance)

        # Try to get the cached LBD probability (if not in the cache, compute it and cache it)
        lbd_probability = cache_instance.get_cached_lbd_probability()
        if lbd_probability:
            return lbd_probability

        # Predict the LBD probability
        lbd_probability = predict_lbd_probability(user, process_features(instance), cls.predictor)

        # Cache the predicted LBD probability (if not None)
        if lbd_probability is not None:
            cache_instance.set_cached_lbd_probability(lbd_probability)

        # Predict the LBD probability
        return lbd_probability

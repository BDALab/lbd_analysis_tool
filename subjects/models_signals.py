import uuid
import secrets
from predictor.client import register_predictor_user
from django.core.cache import cache


# Define the signals
def prepare_predictor_api_for_created_user(sender, instance, created, **kwargs):
    """
    Prepares the predictor API for the created user.

    :param sender: sender class
    :type sender: User
    :param instance: instance object
    :type instance: User instance
    :param created: creation flag (True if created; False otherwise)
    :type created bool
    :param kwargs: additional keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None type
    """

    if created:

        # Add username and password for predictor API after user is created
        instance.predictor_username = str(uuid.uuid4())
        instance.predictor_password = secrets.token_urlsafe(sender.PREDICTOR_PASSWORD_LENGTH)

        # Sign-up the user in the predictor API
        if register_predictor_user(instance):
            instance.predictor_registered = True

        # Save the updated instance
        instance.save()


def invalidate_cached_lbd_prediction_for_session(sender, instance, created, **kwargs):
    """
    Invalidates the cached LBD prediction for an examination session.

    :param sender: sender class
    :type sender: child class of CommonExaminationSessionData
    :param instance: instance object
    :type instance: child instance of CommonExaminationSessionData
    :param created: creation flag (True if created; False otherwise)
    :type created bool
    :param kwargs: additional keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None type
    """

    # Get the keys to be invalidated (specific session and subject)
    session_key = f'{instance.get_lbd_probability_cache_key_for_session()}'
    subject_key = f'{instance.get_lbd_probability_cache_key_for_subject()}'

    # Join the obtained keys
    keys = [session_key] + [subject_key]

    # Invalidate the keys
    if keys:
        cache.delete_many(keys)


def invalidate_cached_lbd_prediction_for_subject(sender, instance, created, **kwargs):
    """
    Invalidates the cached LBD prediction for a subject.

    :param sender: sender class
    :type sender: Subject
    :param instance: instance object
    :type instance: Subject instance
    :param created: creation flag (True if created; False otherwise)
    :type created bool
    :param kwargs: additional keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None type
    """
    cache.delete(instance.get_lbd_probability_cache_key())

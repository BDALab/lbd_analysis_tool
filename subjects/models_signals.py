from predictor import sign_up_predictor_user
from django.conf import settings
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
        instance.predictor_username = instance.generate_predictor_username()
        instance.predictor_password = instance.generate_predictor_password()

        # Sign-up the user in the predictor API
        if getattr(settings, 'PREDICTOR_CONFIGURATION', {}).get('use_api_predictor', False) is True:
            sign_up_predictor_user(user=instance)

        # Save the updated instance
        instance.save()


def update_last_examined_on_for_subject(sender, instance, created, **kwargs):
    """
    Updates the last examined on timestamp for the subject.

    :param sender: sender class
    :type sender: User
    :param instance: instance object
    :type instance: ExaminationSession instance
    :param created: creation flag (True if created; False otherwise)
    :type created bool
    :param kwargs: additional keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None type
    """

    # Get the timestamps for the subject's examination sessions
    examined_on = [
        session.examined_on for session in instance.get_sessions(subject=instance.subject)
        if session.examined_on
    ]

    # Update the last examined on of the subject
    if examined_on:
        instance.subject.last_examined_on = max(examined_on)
        instance.subject.save()


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
    session_key = f'{instance.examination_session.get_lbd_probability_cache_key()}'
    subject_key = f'{instance.examination_session.subject.get_lbd_probability_cache_key()}'

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

from django.conf import settings
from django.http import HttpResponse
from django.core.cache import cache
from predictor.client import predict_lbd_probability
from .models_cache import CACHE_TTL


def export_data(request, code, session_number, model):
    """
    Exports the data in a CSV file that is downloaded in a browser.

    :param request: HTTP request
    :type request: Request
    :param code: code of the subject
    :type code: str
    :param session_number: session number
    :type session_number: str
    :param model: model to be used to get the data to be exported
    :type model: Model
    :return: HTTP response for the data to be exported
    :rtype: HttpResponse
    """

    # Prepare the HTTP response and the fetched data to be exported
    response = HttpResponse(content_type='text/csv')
    fetched = model.get_data(subject_code=code, session_number=session_number)

    # Prepare the fetched data to be downloadable
    response = model.prepare_downloadable(record=fetched, response=response)

    # Set the content disposition (to be downloaded by a browser)
    response['Content-Disposition'] = 'attachment; filename="exported.csv"'

    # Return the HTTP response
    return response


def predict_lbd_probability_for_session(user, session):
    """Predicts the LBD probability for a session data"""

    # Prepare the data and the model for the prediction
    data = session.get_features_for_prediction()
    model = getattr(settings, 'PREDICTOR_CONFIGURATION')['predictor_model_identifier']

    # Predict the LBD probability
    return predict_lbd_probability(user, data, model)


# TODO: what if there are more than 1 sessions with the data? Use mean values for the features?)
def predict_lbd_probability_for_subject(user, subject, session_model):
    """Predicts the LBD probability for the latest session data of a subject"""

    # Get the examination sessions of a subject (order from newest to oldest)
    sessions = session_model.get_sessions(subject=subject, order_by=('-session_number',))

    # If there are no session so far, return None
    if not sessions.first():
        return None

    # Predict the LBD probability (from the latest session with the data)
    for session in sessions:
        predicted = predict_lbd_probability_for_session(user, session)
        if predicted:
            return predicted


def get_cached_lbd_probability_for_session(user, session):
    """Gets the cached LBD probability for the session"""

    # Construct the cache key
    cache_key = session.get_lbd_probability_cache_key()

    # Get the LBD probability (handle caching)
    if cache.get(cache_key):
        lbd_probability = cache.get(cache_key)
    else:
        lbd_probability = predict_lbd_probability_for_session(user, session)

        # Cache the predicted value (if it's a valid prediction)
        if lbd_probability is not None:
            cache.set(cache_key, lbd_probability, timeout=CACHE_TTL)

    # Return the LBD probability
    return lbd_probability


def get_cached_lbd_probability_for_subject(user, subject, session_model):
    """Gets the cached LBD probability for the subject"""

    # Construct the cache key
    cache_key = subject.get_lbd_probability_cache_key()

    # Get the LBD probability (handle caching)
    if cache.get(cache_key):
        lbd_probability = cache.get(cache_key)
    else:
        lbd_probability = predict_lbd_probability_for_subject(user, subject, session_model)

        # Cache the predicted value (if it's a valid prediction)
        if lbd_probability is not None:
            cache.set(cache_key, lbd_probability, timeout=CACHE_TTL)

    # Return the LBD probability
    return lbd_probability

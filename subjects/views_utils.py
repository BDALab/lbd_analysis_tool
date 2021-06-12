from django.conf import settings
from django.http import HttpResponse
from predictor.client import predict_lbd_probability


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

    # Prepare the data (from the current examination session) and the model for the prediction
    data = session.get_features_for_prediction()
    model = getattr(settings, 'PREDICTOR_CONFIGURATION')['predictor_model_identifier']

    # Predict the LBD probability
    return predict_lbd_probability(user, data, model)


# TODO: what if there is already an older session with the data? (go back until there is a session with the data?)
def predict_lbd_probability_for_subject(user, subject, session_model):
    """Predicts the LBD probability for the latest session data of a subject"""

    # Get the examination sessions of a subject
    sessions = session_model.get_sessions(subject=subject, order_by=('session_number',))

    # Predict the LBD probability
    return predict_lbd_probability_for_session(user, sessions.last()) if sessions.last() else None

from http import HTTPStatus
from django.conf import settings
from predictor.client import LBDPredictorApiClient, LBDPredictorLocalClient


def predict_lbd_probability(user, data, model):
    """
    Predicts the LBD probability via the Predictor API.

    :param user: user model instance
    :type user: User instance
    :param data: data to be used for the prediction
    :type data: data supported by the API
    :param model: model identifier to be used
    :type model: str
    :return: predicted LBD probability
    :rtype: float
    """

    # Prepare the LBD predictor using the provided user instance
    if getattr(settings, 'PREDICTOR_CONFIGURATION', {}).get('use_api_predictor', False) is True:
        predictor = LBDPredictorApiClient(user)
    else:
        predictor = LBDPredictorLocalClient()

    # Validate if there are data to be used for the prediction
    labels, values = data
    if values.size == 0:
        return None

    # Predict the LBD probability via the LBD predictor using the provided data and model identifier
    response, status_code = predictor.predict_proba(data=data, model=model)

    # Get the LBD probability
    if status_code == HTTPStatus.OK:
        probability = response.get('predicted') if response else None
        probability = round(float(probability[0, 1]) * 100, 2) if probability is not None else None
    else:
        probability = None

    # Return the predicted LBD probability
    return probability


def sign_up_predictor_user(user=None, predictor=None):
    """
    Signs-up a new predictor user.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: LBD predictor API instance
    :type predictor: LBDPredictorApiClient, optional
    :return: True if signed-up, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to sign-up a user (user/LBDPredictorApiClient)')

    # Sign-up a new user
    _, status_code = (predictor or LBDPredictorApiClient(user)).sign_up()

    # Return the information about the user sign-up
    return True if status_code == HTTPStatus.OK else False


def log_in_predictor_user(user=None, predictor=None):
    """
    Logs-in the predictor user.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: LBD predictor API instance
    :type predictor: LBDPredictorApiClient, optional
    :return: True if logged-in, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to log-in a user (user/LBDPredictorApiClient)')

    # Log-in the user
    _, status_code = (predictor or LBDPredictorApiClient(user)).log_in()

    # Return the information about the user log-in
    return True if status_code == HTTPStatus.OK else False


def refresh_access_token(user=None, predictor=None):
    """
    Refreshes the access token.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: LBD predictor API instance
    :type predictor: LBDPredictorApiClient, optional
    :return: True if the access token is refreshed, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to refresh the access token (user/LBDPredictorApiClient)')

    # Refresh the access token
    _, status_code = (predictor or LBDPredictorApiClient(user)).refresh_access_token()

    # Return the information about the access token refresh
    return True if status_code == HTTPStatus.OK else False

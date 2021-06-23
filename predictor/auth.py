import requests
from predictor.client import PredictorApiClient


def sign_up_predictor_user(user=None, predictor=None):
    """
    Signs-up (registers) the predictor user.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: predictor API instance
    :type predictor: object, optional
    :return: True if registered, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to sign-up a user (user/PredictorAPIClient)')

    # Prepare the predictor API client using the provided user instance
    predictor = predictor if predictor else PredictorApiClient(user)

    # Get the user
    user = (user if user else predictor.user)

    # Sign-up the user and set the registration flag if needed
    try:
        predictor.sign_up()
    except requests.ConnectionError:
        return False
    else:
        user.predictor_registered = True
        user.save()
        return True


def log_in_predictor_user(user=None, predictor=None):
    """
    Logs-in the predictor user.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: predictor API instance
    :type predictor: object, optional
    :return: authorization token
    :rtype: str
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to sign-up a user (user/PredictorAPIClient)')

    # Prepare the predictor API client using the provided user instance
    predictor = predictor if predictor else PredictorApiClient(user)

    # Log-in the user
    try:
        return predictor.log_in().json().get('token')
    except requests.ConnectionError:
        return ''

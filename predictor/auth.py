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
        response = predictor.sign_up()
    except requests.ConnectionError:
        return False
    else:
        if response.ok:
            user.predictor_registered = True
            user.save()
            return True
        return False


def log_in_predictor_user(user=None, predictor=None):
    """
    Logs-in the predictor user.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: predictor API instance
    :type predictor: object, optional
    :return: True if logged-in, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to sign-up a user (user/PredictorAPIClient)')

    # Prepare the predictor API client using the provided user instance
    predictor = predictor if predictor else PredictorApiClient(user)

    # Get the user
    user = (user if user else predictor.user)

    # Log-in the user
    try:
        response = predictor.log_in()
    except requests.ConnectionError:
        return False
    else:
        if response.ok:
            user.predictor_access_token = response.json().get('access_token')
            user.predictor_refresh_token = response.json().get('refresh_token')
            user.save()
            return True
        return False


def refresh_access_token(user=None, predictor=None):
    """
    Refreshes the access token.

    :param user: user model instance
    :type user: User instance, optional
    :param predictor: predictor API instance
    :type predictor: object, optional
    :return: True if the access token is refreshed, False otherwise
    :rtype: bool
    """

    # Validate the input arguments
    if not any((user, predictor)):
        raise ValueError(f'Not enough arguments to sign-up a user (user/PredictorAPIClient)')

    # Prepare the predictor API client using the provided user instance
    predictor = predictor if predictor else PredictorApiClient(user)

    # Get the user
    user = (user if user else predictor.user)

    # Log-in the user
    try:
        response = predictor.refresh_access_token()
    except requests.ConnectionError:
        return False
    else:
        if response.ok:
            user.predictor_access_token = response.json().get('access_token')
            user.save()
            return True
        return False

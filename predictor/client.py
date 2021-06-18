import requests
import json_tricks
from django.conf import settings


class PredictorApiClient(object):
    """Class implementing the Predictor API client"""

    # Define the HTTP error codes to be handled by the re-logging
    log_in_required_errors = [401, 422]

    # Define the predictor settings
    address = getattr(settings, 'PREDICTOR_CONFIGURATION').get('address')
    timeout = getattr(settings, 'PREDICTOR_CONFIGURATION').get('timeout')

    def __init__(self, user):
        self.user = user

    def sign_up(self):
        """Signs-up a user in the predictor API"""
        return requests.post(f'{self.address}/signup', json=self.user.get_predictor_authentication_data())

    def log_in(self):
        """Logs-in a user in the predictor API"""
        return requests.post(f'{self.address}/login', json=self.user.get_predictor_authentication_data())

    def predict(self, data=None, model=None):
        """
        Predicts the LBD probability via the predictor API.

        :param data: data to be used for the prediction
        :type data: data supported by the API
        :param model: model identifier to be used
        :type model: str
        :return: API response
        :rtype: Response
        """

        # Prepare the data to be sent via the API
        data = {
            'features': {'data': self.wrap_data(data)},
            'model': model
        }

        # Prepare the headers to be sent via the API
        headers = self.user.get_predictor_authorization_data()

        # Run the predictor
        return requests.post(
            url=f'{self.address}/predict',
            json=data,
            headers=headers,
            verify=True,
            timeout=self.timeout)

    @staticmethod
    def unwrap_data(data):
        """Unwraps the data (deserialize from JSON-string to numpy.ndarray)"""
        return json_tricks.loads(data) if isinstance(data, str) else data

    @staticmethod
    def wrap_data(data):
        """Wraps the data (serialize numpy.ndarray to JSON-string)"""
        return json_tricks.dumps(data, allow_nan=True) if not isinstance(data, str) else data


def register_predictor_user(user):
    """
    Registers the predictor user.

    :param user: user model instance
    :type user: User instance
    :return: True if registered, False otherwise
    :rtype: bool
    """

    # Prepare the predictor API client using the provided user instance
    predictor = PredictorApiClient(user)

    # Register the user
    try:
        predictor.sign_up()
    except requests.ConnectionError:
        return False
    else:
        return True


def predict_lbd_probability(user, data, model):
    """
    Predicts the LBD probability via the predictor API.

    :param user: user model instance
    :type user: User instance
    :param data: data to be used for the prediction
    :type data: data supported by the API
    :param model: model identifier to be used
    :type model: str
    :return: predicted LBD probability
    :rtype: float
    """

    # Prepare the predictor API client using the provided user instance
    predictor = PredictorApiClient(user)

    # Check and validate the registration of the user
    if not user.predictor_registered:
        if not register_predictor_user(user):
            return None

    # Validate if there are data to be used for the prediction
    labels, values = data
    if values.size == 0:
        return None

    try:

        # Predict the LBD probability via the predictor API using the provided data and model identifier
        response = predictor.predict(data=data, model=model)

        # Handle the authorization token errors
        if not response.ok:
            if response.status_code in predictor.log_in_required_errors:
                user.predictor_authorization_token = predictor.log_in().json().get('token')
                user.save()
                response = predictor.predict(data=data, model=model)

        if not response.ok:
            return None

        # Extract the LBD probability
        probability = response.json().get('proba')
        probability = round(float(probability) * 100, 2) if probability is not None else None

    except requests.ConnectionError:
        probability = None

    # Return the LBD probability
    return probability

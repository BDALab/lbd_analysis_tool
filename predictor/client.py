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
        return requests.post(f'{self.address}/signup', json=self.user.get_predictor_authentication_credentials())

    def log_in(self):
        """Logs-in a user in the predictor API"""
        return requests.post(f'{self.address}/login', json=self.user.get_predictor_authentication_credentials())

    def refresh_access_token(self):
        """Refreshes an access token in the predictor API"""
        return requests.post(f'{self.address}/refresh', json=self.user.get_predictor_refresh_token())

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

        # Get feature labels and values
        feature_labels, feature_values = data

        # Prepare the data to be sent via the API
        data = {
            'model': model,
            'features': {
                'data': self.wrap_data(feature_values),
                'labels': feature_labels,
                'shapes': feature_values.shape
            }
        }

        # Prepare the headers to be sent via the API
        headers = self.user.get_predictor_access_token()

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

import os
import pickle
from http import HTTPStatus
from django.conf import settings
from predictor_api_client import PredictorApiClient


# File path
this_path = os.path.dirname(os.path.abspath(__file__))


class LBDPredictorLocalClient(object):
    """Class implementing the LBD Predictor local client"""

    # Define the predictor settings
    model_storage = 'models'

    # TODO: use when real model(s) is(/are) serialized
    # @classmethod
    # def _prepare(cls, model):
    #     with open(os.path.join(this_path, cls.model_storage, f'{model}.pkl'), 'rb') as f:
    #         return pickle.load(f)

    @classmethod
    def _prepare(cls, model):
        from predictor.dummy import DummyPredictor
        return DummyPredictor()

    def predict(self, data, model):
        """
        Predicts the LBD class via the local predictor.

        :param data: data to be used for the prediction
        :type data: data supported by the predictor
        :param model: model identifier to be used
        :type model: str
        :return: (data/error_info, status_code)
        :rtype: tuple
        """

        # Prepare the prediction
        predictor = self._prepare(model)

        # Get feature labels and values
        feature_labels, feature_values = data

        # Run the predictor
        try:
            predicted = predictor.predict(feature_values)
        except Exception as e:
            return None, HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return {'predicted': predicted}, HTTPStatus.OK

    def predict_proba(self, data, model):
        """
        Predicts the LBD probability via the local predictor.

        :param data: data to be used for the prediction
        :type data: data supported by the predictor
        :param model: model identifier to be used
        :type model: str
        :return: (data/error_info, status_code)
        :rtype: tuple
        """

        # Prepare the prediction
        predictor = self._prepare(model)

        # Get feature labels and values
        feature_labels, feature_values = data

        # Run the predictor
        try:
            predicted = predictor.predict_proba(feature_values)
        except Exception as e:
            return None, HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return {'predicted': predicted}, HTTPStatus.OK


class LBDPredictorApiClient(object):
    """Class implementing the LBD Predictor API client"""

    # Define the HTTP error codes to be handled by the re-logging
    log_in_required_errors = [401, 422]

    # Define the predictor settings
    host = getattr(settings, 'PREDICTOR_CONFIGURATION').get('host')
    port = getattr(settings, 'PREDICTOR_CONFIGURATION').get('port')
    verify = getattr(settings, 'PREDICTOR_CONFIGURATION').get('verify')
    timeout = getattr(settings, 'PREDICTOR_CONFIGURATION').get('timeout')

    def __init__(self, user):
        """Constructor method"""

        # Set the predictor API client
        self.client = PredictorApiClient(host=self.host, port=self.port, verify=self.verify, timeout=self.timeout)

        # Set the user model instance
        self.user = user

    def _prepare(self):

        # Check and validate the sign-up of the user
        if not self.user.predictor_registered:
            _, status_code = self.sign_up()
            return True if status_code == HTTPStatus.OK else False

        # Check if the user is logged-in already and if not, call the log-in
        if not self.user.predictor_access_token:
            _, status_code = self.log_in()
            return True if status_code == HTTPStatus.OK else False

        # Return the default positive response if all is well
        return True

    def sign_up(self):
        """Signs-up a user in the predictor API"""

        # Sign up a new user
        response, status_code = self.client.sign_up(**self.user.get_predictor_authentication_credentials())

        # Update the user credentials
        if status_code == HTTPStatus.OK:
            self.user.predictor_registered = True
            self.user.save()

        # Return the response and the status code
        return response, status_code

    def log_in(self):
        """Logs-in a user in the predictor API"""

        # Log in the user
        response, status_code = self.client.log_in(**self.user.get_predictor_authentication_credentials())

        # Update the user credentials
        if status_code == HTTPStatus.OK:
            self.user.predictor_access_token = self.client.access_token
            self.user.predictor_refresh_token = self.client.refresh_token
            self.user.save()

        # Return the response and the status code
        return response, status_code

    def refresh_access_token(self):
        """Refreshes an access token in the predictor API"""

        # Refresh the user access token
        response, status_code = self.client.refresh_access_token(self.user.get_predictor_refresh_token())

        # Update the user credentials
        if status_code == HTTPStatus.OK:
            self.user.predictor_access_token = self.client.access_token
            self.user.save()

        # Return the response and the status code
        return response, status_code

    def predict(self, data, model):
        """
        Predicts the LBD class via the predictor API.

        :param data: data to be used for the prediction
        :type data: data supported by the API
        :param model: model identifier to be used
        :type model: str
        :return: (data/error_info, status_code)
        :rtype: tuple
        """

        # Prepare the prediction
        if not self._prepare():
            return None

        # Get feature labels and values
        feature_labels, feature_values = data

        # Run the predictor
        response, status_code = self.client.predict(
            access_token=self.user.get_predictor_access_token(),
            refresh_token=self.user.get_predictor_refresh_token(),
            model_identifier=model,
            feature_values=feature_values,
            feature_labels=feature_labels)

        # Update the user credentials
        if status_code == HTTPStatus.OK:
            if self.client.access_token and self.client.access_token != self.user.predictor_access_token:
                self.user.predictor_access_token = self.client.access_token
                self.user.save()

        # Return the response and the status code
        return response, status_code

    def predict_proba(self, data, model):
        """
        Predicts the LBD probability via the predictor API.

        :param data: data to be used for the prediction
        :type data: data supported by the API
        :param model: model identifier to be used
        :type model: str
        :return: (data/error_info, status_code)
        :rtype: tuple
        """

        # Prepare the prediction
        if not self._prepare():
            return None

        # Get feature labels and values
        feature_labels, feature_values = data

        # Run the predictor
        response, status_code = self.client.predict_proba(
            access_token=self.user.get_predictor_access_token(),
            refresh_token=self.user.get_predictor_refresh_token(),
            model_identifier=model,
            feature_values=feature_values,
            feature_labels=feature_labels)

        # Update the user credentials
        if status_code == HTTPStatus.OK:
            if self.client.access_token and self.client.access_token != self.user.predictor_access_token:
                self.user.predictor_access_token = self.client.access_token
                self.user.save()

        # Return the response and the status code
        return response, status_code

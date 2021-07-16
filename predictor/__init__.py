import requests
from predictor.client import PredictorApiClient
from predictor.auth import sign_up_predictor_user, log_in_predictor_user, refresh_access_token


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
        if not sign_up_predictor_user(predictor=predictor):
            return None

    # Check if the use is logged-in already (log-in if needed)
    if not user.predictor_access_token:
        if not log_in_predictor_user(predictor=predictor):
            return None

    # Validate if there are data to be used for the prediction
    labels, values = data
    if values.size == 0:
        return None

    try:

        # Predict the LBD probability via the predictor API using the provided data and model identifier
        response = predictor.predict_proba(data=data, model=model)

        # Handle the authorization token expiration
        if not response.ok:
            if response.status_code in predictor.log_in_required_errors:
                if refresh_access_token(predictor=predictor):
                    response = predictor.predict_proba(data=data, model=model)

        if not response.ok:
            return None

        # Extract the LBD probability
        probability = predictor.unwrap_data(response.json().get('predicted'))
        probability = round(float(probability[0, 1]) * 100, 2) if probability is not None else None

    except requests.ConnectionError:
        probability = None

    # Return the LBD probability
    return probability

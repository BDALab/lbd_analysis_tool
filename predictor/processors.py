import numpy


def process_features(session):
    """Gets/processes the features for prediction"""

    # Get the feature labels and values for the data to be used for prediction
    #
    # Features are composed of the following objects:
    #  1. subject
    #  2. session <- questionnaire, feature-based data, ...
    subject_feature_labels, subject_feature_values = session.subject.get_features_for_prediction()
    session_feature_labels, session_feature_values = session.get_features_for_prediction()

    # Combine the feature labels and values
    feature_labels = subject_feature_labels + session_feature_labels
    feature_values = numpy.hstack((subject_feature_values, session_feature_values))

    # Return the features
    return feature_labels, feature_values

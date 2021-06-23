from predictor.transformers import NominalFeatureTransformer, OrdinalFeatureTransformer, NumericalFeatureTransformer


# Define te features preprocessors mapping (mapping: type-transformer)
FEATURES_PREPROCESSORS = {
    "nominal": NominalFeatureTransformer,
    "ordinal": OrdinalFeatureTransformer,
    "numerical": NumericalFeatureTransformer
}


def preprocess_feature(feature_value, feature_label, model):
    """
    Preprocesses the feature value and label.

    :param feature_value: feature value
    :type feature_value: str
    :param feature_label: feature label
    :type feature_label: str
    :param model: model to get the features description from
    :type model: object-like
    :return: transformed features and labels
    :rtype: tuple
    """

    # Get the feature type and the associated feature preprocessor
    feature_type = model.CONFIGURATION.get_feature_type(feature_label)
    preprocessor = FEATURES_PREPROCESSORS[feature_type]

    # Preprocess the feature
    return preprocessor.transform(feature_value, feature_label, model=model)

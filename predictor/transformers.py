class BaseTransformer(object):
    """Base class for the feature transformers"""

    @classmethod
    def transform(cls, feature_value, feature_label, model):
        """
        Transforms the features into numerical form.

        :param feature_value: value of the feature
        :type feature_label: str/numerical/None
        :param feature_label: label of the feature
        :type feature_label: str
        :param model: model
        :type model: object-like
        :return: transformed labels, features
        :rtype: tuple (label: list, value: list)
        """
        return [feature_label], [feature_value]


class NominalFeatureTransformer(BaseTransformer):
    """Class implementing nominal feature transformer"""

    @classmethod
    def transform(cls, feature_value, feature_label, model):

        # Get the categories
        categories = model.CONFIGURATION.get_feature_options(feature_label)

        # Convert the nominal feature and label into numerical category form
        feature_value = [0 if feature_value != category else 1 for category in categories]
        feature_label = [f'{feature_label}_{category}' for category in categories]

        # Return the transformed labels and features
        return feature_label, feature_value


class OrdinalFeatureTransformer(BaseTransformer):
    """Class implementing ordinal feature transformer"""

    @classmethod
    def transform(cls, feature_value, feature_label, model):

        # Get the categories
        categories = model.CONFIGURATION.get_feature_order(feature_label)

        # Prepare the ordinal-numerical mapping
        categories = {c: i for i, c in enumerate(categories, 1)}

        # Convert the ordinal feature into numerical category form
        feature_value = [categories.get(feature_value, None)]
        feature_label = [feature_label]

        # Return the transformed labels and features
        return feature_label, feature_value


class NumericalFeatureTransformer(BaseTransformer):
    """Class implementing numerical feature transformer"""
    pass

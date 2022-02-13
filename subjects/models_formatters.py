import csv
import pandas


class FeaturesFormatter(object):
    """Class implementing models features formatter"""

    # Define the feature label/value field names
    FEATURE_LABEL_FIELD = 'label'
    FEATURE_TITLE_FIELD = 'title'
    FEATURE_VALUE_FIELD = 'value'

    # Define the unfilled feature label/title/value representation and real value
    UNFILLED_FEATURE_LABEL_REPR = ''
    UNFILLED_FEATURE_LABEL_REAL = None
    UNFILLED_FEATURE_TITLE_REPR = 'title'
    UNFILLED_FEATURE_TITLE_REAL = None
    UNFILLED_FEATURE_VALUE_REPR = ''
    UNFILLED_FEATURE_VALUE_REAL = None

    # Define the maximum feature label length to be shown/used
    MAX_FEATURE_LABEL_LENGTH_PRESENTABLE = 100
    MAX_FEATURE_LABEL_LENGTH_COMPUTABLE = None

    def __init__(self, model):
        self.model = model

    @classmethod
    def adjust_feature_label_for_presentation(cls, label=None):
        """Adjusts the feature label for presentation"""
        return label

    @classmethod
    def adjust_feature_title_for_presentation(cls, title):
        """Adjusts the feature title for presentation"""
        if not title or title == cls.UNFILLED_FEATURE_TITLE_REAL:
            return cls.UNFILLED_FEATURE_TITLE_REPR
        else:
            return title

    @classmethod
    def adjust_feature_value_for_presentation(cls, value):
        """Adjusts the feature value for presentation"""
        if not value or value == cls.UNFILLED_FEATURE_VALUE_REAL:
            return cls.UNFILLED_FEATURE_VALUE_REPR
        else:
            return round(value, 4) if isinstance(value, float) else value

    @classmethod
    def adjust_feature_label_for_computation(cls, label):
        """Adjusts the feature label for computation"""
        return label

    @classmethod
    def adjust_feature_value_for_computation(cls, value):
        """Adjusts the feature value for computation"""
        if isinstance(value, str) and value in cls.UNFILLED_FEATURE_VALUE_REPR:
            return cls.UNFILLED_FEATURE_VALUE_REAL
        else:
            return value

    @classmethod
    def sanitize_feature_label(cls, label):
        """Sanitizes the feature label (adjusts the length of the label"""
        if label and len(label) > cls.MAX_FEATURE_LABEL_LENGTH_PRESENTABLE:
            label = f'{label[:cls.MAX_FEATURE_LABEL_LENGTH_PRESENTABLE]}...'
        return label

    @classmethod
    def sanitize_feature_value(cls, feature):
        """Sanitizes the feature value (replaces NaN with None)"""
        return None if (isinstance(feature, str) and not feature) or (pandas.isna(feature)) else feature

    def prepare_presentable(self, record=None, features=None, **kwargs):
        """
        Prepares the features to be presentable.

        :param record: record
        :type record: Record, optional
        :param features: features
        :type features: list of dicts, optional
        :return: features in a presentable form
        :rtype: list of dicts
        """

        # Validate the input arguments
        if not any((record, features)):
            raise ValueError(f'Not enough information: record or features must be provided')

        # Get the features
        features = self.model.get_features_from_record(record, **kwargs) if not features else features

        # Return the presentable features
        return [{
            self.FEATURE_LABEL_FIELD:
                self.adjust_feature_label_for_presentation(feature.get(self.FEATURE_LABEL_FIELD)),
            self.FEATURE_TITLE_FIELD:
                self.adjust_feature_title_for_presentation(feature.get(self.FEATURE_TITLE_FIELD)),
            self.FEATURE_VALUE_FIELD:
                self.adjust_feature_value_for_presentation(feature.get(self.FEATURE_VALUE_FIELD))
            } for feature in features
        ]

    def prepare_computable(self, record=None, features=None):
        """
        Prepares the features to be computable.

        :param record: record
        :type record: Record, optional
        :param features: features
        :type features: list of dicts, optional
        :return: features in a computable form
        :rtype: list of dicts
        """

        # Validate the input arguments
        if not any((record, features)):
            raise ValueError(f'Not enough information: record or features must be provided')

        # Get the features
        features = self.model.get_features_from_record(record) if not features else features

        # Return the computable features
        return [{
            self.FEATURE_LABEL_FIELD: self.adjust_feature_label_for_computation(feature[self.FEATURE_LABEL_FIELD]),
            self.FEATURE_VALUE_FIELD: self.adjust_feature_value_for_computation(feature[self.FEATURE_VALUE_FIELD])
            } for feature in features
        ]

    def prepare_downloadable(self, response, record=None, features=None):
        """
        Prepares the features to be downloadable.

        :param response: response to be filled with the features
        :type response: HttpResponse
        :param record: record
        :type record: Record, optional
        :param features: features
        :type features: list of dicts, optional
        :return: response with the inserted data
        :rtype: HttpResponse
        """

        # Validate the input arguments
        if not any((record, features)):
            raise ValueError(f'Not enough information: record or features must be provided')

        # Get the features
        features = self.model.get_features_from_record(record) if not features else features

        # Prepare the CSV writer
        writer = csv.writer(response)

        # Write the header and the body
        writer.writerow([element.get(self.FEATURE_LABEL_FIELD) for element in features])
        writer.writerow([element.get(self.FEATURE_VALUE_FIELD) for element in features])

        # Return the response
        return response

    @classmethod
    def get_features_as_kwargs(cls, features):
        """Returns the features as kwargs (dict to be unfolded)"""
        return {
            feature[cls.FEATURE_LABEL_FIELD]:
                cls.sanitize_feature_value(feature[cls.FEATURE_VALUE_FIELD])
            for feature in features
        }

    @classmethod
    def get_features_as_dataframe(cls, features):
        """Returns the features as pandas DataFrame"""
        return pandas.DataFrame([{
            feature[cls.FEATURE_LABEL_FIELD]: cls.sanitize_feature_value(feature[cls.FEATURE_VALUE_FIELD])}
            for feature in features
        ])


def format_feature_data_type(feature, configuration):
    """
    Formats the feature data type.

    :param feature: value of the feature
    :type feature: int, float, str, None or np.NaN
    :param configuration: configuration of the feature
    :return: formatted feature
    :rtype: int, float, str or np.NaN
    """

    # Validate the input values
    if not feature:
        return None
    if not configuration:
        return feature

    # Get the feature type
    feature_type = configuration.get("type", "numerical")

    # Format the data type
    if feature_type == "numerical":
        return float(feature) if configuration.get("data_type", "float") else int(feature)
    else:
        data_type = configuration.get("data_type", "str")
        if data_type not in ("str", "int"):
            raise TypeError(f"Unsupported feature type {feature} ({type(feature)})")
        if data_type == "str":
            return str(feature)
        if data_type == "int":
            return int(float(feature))

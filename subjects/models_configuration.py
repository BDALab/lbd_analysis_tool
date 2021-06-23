import os
from django.conf import settings


class CommonDataConfiguration(object):
    """Base class for data configuration"""

    # Define the configuration
    database = None
    predictor = None

    # Define the serialization of the features
    serialized_features = False

    @classmethod
    def get_form_fields(cls):
        """Returns the form fields"""
        return cls.database.get('form_fields', [])

    @classmethod
    def get_available_feature_names(cls):
        """Returns the feature names"""
        return cls.database.get('features')

    @classmethod
    def get_predictor_feature_names(cls):
        """Returns the feature names used by the predictor"""
        return cls.predictor.get('features')

    @classmethod
    def get_features_description(cls):
        """Returns the features description"""
        return cls.database.get('features_description', {})

    @classmethod
    def get_feature_description(cls, feature_name):
        """Returns the feature description"""
        return cls.get_features_description().get(feature_name, {})

    @classmethod
    def get_feature_type(cls, feature_name):
        """Returns the type of the feature"""
        return cls.get_feature_description(feature_name).get('type')

    @classmethod
    def get_feature_options(cls, feature_name):
        """Returns the options of the feature"""
        return cls.get_feature_description(feature_name).get('options')

    @classmethod
    def get_feature_order(cls, feature_name):
        """Returns the order of the feature"""
        return cls.get_feature_description(feature_name).get('order')

    @classmethod
    def is_feature_nominal(cls, feature_name):
        """Returns if the feature is nominal"""
        return cls.get_feature_type(feature_name) == 'nominal'

    @classmethod
    def is_feature_ordinal(cls, feature_name):
        """Returns if the feature is nominal"""
        return cls.get_feature_type(feature_name) == 'ordinal'

    @classmethod
    def is_feature_numerical(cls, feature_name):
        """Returns if the feature is numerical"""
        return cls.get_feature_type(feature_name) == 'numerical'


class CommonDataQuestionnaireBasedConfiguration(CommonDataConfiguration):
    """Base class for questionnaire based configuration"""

    @classmethod
    def get_questionnaire(cls):
        """Returns the questionnaire (list of dicts)"""
        return [item for item in cls.database.get('questionnaire')]

    @classmethod
    def get_questions(cls):
        """Returns the questionnaire questions"""
        return [item['question'] for item in cls.get_questionnaire()]


class CommonDataFeatureBasedConfiguration(CommonDataConfiguration):
    """Base class for feature based configuration"""

    # Define the serialization of the features
    serialized_features = True

    # Define the data field
    data_field = 'data'

    # Define the data path
    data_path = os.path.join(getattr(settings, 'MEDIA_ROOT'), data_field)


class DataQuestionnaireConfiguration(CommonDataQuestionnaireBasedConfiguration):
    """Class implementing questionnaire data configuration"""

    # Load the configuration
    database = getattr(settings, 'DATA_CONFIGURATION')['data']['session']['questionnaire']
    predictor = getattr(settings, 'PREDICTOR_CONFIGURATION')['data']['session']['questionnaire']


class DataAcousticConfiguration(CommonDataFeatureBasedConfiguration):
    """Class implementing acoustic data configuration"""

    # Load the configuration
    database = getattr(settings, 'DATA_CONFIGURATION')['data']['session']['acoustic']
    predictor = getattr(settings, 'PREDICTOR_CONFIGURATION')['data']['session']['acoustic']


class SubjectDataConfiguration(CommonDataConfiguration):
    """Class implementing subject data configuration"""

    # Load the configuration
    database = getattr(settings, 'DATA_CONFIGURATION')['data']['subject']
    predictor = getattr(settings, 'PREDICTOR_CONFIGURATION')['data']['subject']

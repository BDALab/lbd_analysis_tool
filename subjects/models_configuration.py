from django.conf import settings


class CommonDataConfiguration(object):
    """Base class for data configuration"""

    # Load the configuration
    configuration = None

    @classmethod
    def get_feature_names(cls):
        """Returns the feature names"""
        return cls.configuration.get('features')

    @classmethod
    def get_predictor_feature_names(cls):
        """Returns the feature names used by the predictor"""
        return cls.configuration.get('predictor_features')


class CommonDataQuestionnaireBasedConfiguration(CommonDataConfiguration):
    """Base class for questionnaire based configuration"""

    @classmethod
    def get_questionnaire(cls):
        """Returns the questionnaire (list of dicts)"""
        return [item for item in cls.configuration.get('questionnaire')] if cls.configuration else []

    @classmethod
    def get_questions(cls):
        """Returns the questionnaire questions (list: [question 1, ...])"""
        return [item['question'] for item in cls.get_questionnaire()]

    @classmethod
    def get_options(cls):
        """Returns the questionnaire options (list: [[(i, option), ...]])"""
        return [
            [(number, option) for number, option in enumerate(questionnaire_item["options"], 1)]
            for questionnaire_item in cls.get_questionnaire()
        ]


class CommonDataFeatureBasedConfiguration(CommonDataConfiguration):
    """Base class for feature based configuration"""
    pass


class DataQuestionnaireConfiguration(CommonDataQuestionnaireBasedConfiguration):
    """Class implementing questionnaire data configuration"""

    # Load the configuration
    configuration = getattr(settings, 'DATA_QUESTIONNAIRE')


class DataAcousticConfiguration(CommonDataFeatureBasedConfiguration):
    """Class implementing acoustic data configuration"""

    # Load the configuration
    configuration = getattr(settings, 'DATA_ACOUSTIC')

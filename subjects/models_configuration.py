from django.conf import settings


class CommonDataQuestionnaireBasedConfiguration(object):
    """Base class for questionnaire based configuration"""

    # Load the configuration
    configuration = None

    def get_questionnaire(self):
        """Returns the questionnaire (list of dicts)"""
        return [item for item in self.configuration.get('questionnaire')] if self.configuration else []

    def get_feature_names(self):
        """Returns the feature names (question names)"""
        return [item['name'] for item in self.get_questionnaire()]

    def get_questions(self):
        """Returns the questionnaire questions (list: [question 1, ...])"""
        return [item['question'] for item in self.get_questionnaire()]

    def get_options(self):
        """Returns the questionnaire options (list: [[(i, option), ...]])"""
        return [
            [(number, option) for number, option in enumerate(questionnaire_item["options"], 1)]
            for questionnaire_item in self.get_questionnaire()
        ]


class CommonDataFeatureBasedConfiguration(object):
    """Base class for feature based configuration"""

    # Load the configuration
    configuration = None

    def get_feature_names(self):
        """Returns the feature names"""
        return self.configuration.get('features')


class DataQuestionnaireConfiguration(CommonDataQuestionnaireBasedConfiguration):
    """Class implementing questionnaire data configuration"""

    # Load the configuration
    configuration = getattr(settings, 'DATA_QUESTIONNAIRE')


class DataAcousticConfiguration(CommonDataFeatureBasedConfiguration):
    """Class implementing acoustic data configuration"""

    # Load the configuration
    configuration = getattr(settings, 'DATA_ACOUSTIC')

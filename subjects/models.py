import csv
import numpy
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.shortcuts import get_object_or_404
from .models_configuration import DataAcousticConfiguration, DataQuestionnaireConfiguration
from .models_signals import *
from .models_cache import *
from .models_utils import (
    is_csv_file,
    is_excel_file,
    read_features_from_csv,
    read_features_from_excel,
)


class User(AbstractUser):
    """Class implementing user model"""

    # Define the predictor API attributes
    PREDICTOR_PASSWORD_LENGTH = 20

    # Define the model schema
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    predictor_username = models.CharField('predictor username', max_length=50, null=True, blank=True)
    predictor_password = models.CharField('predictor password', max_length=50, null=True, blank=True)
    predictor_authorization_token = models.CharField('predictor token', max_length=300, null=True, blank=True)

    def get_predictor_authentication_data(self):
        """Returns the authentication data for the user instance"""
        return {
            'username': self.predictor_username,
            'password': self.predictor_password
        }

    def get_predictor_authorization_data(self):
        """Returns the authorization data for the user instance"""
        return {'Authorization': f'Bearer {self.predictor_authorization_token}'}


class Organization(models.Model):
    """Class implementing organization model"""

    # Define the model schema
    name = models.CharField('organization name', max_length=50, unique=True)

    def __str__(self):
        return f'Organization: {self.name}'


class Subject(models.Model):
    """Class implementing subject model"""

    class Meta:
        """Model meta information definition"""

        # Default ordering of the records
        ordering = ['code']

    # Define the sex options for each subject
    SEX = [('M', 'Male'), ('F', 'Female')]

    # Define the model schema
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField('subject code', max_length=50, unique=True)
    age = models.SmallIntegerField('age (years)')
    sex = models.CharField('sex', max_length=1, choices=SEX)
    nationality = models.CharField('nationality', max_length=50, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)
    diagnosed = models.BooleanField('diagnosed', default=False)
    lbd_probability = models.FloatField('lbd_probability', null=True, blank=True)
    description = models.CharField('description', max_length=255, blank=True)

    def __str__(self):
        return f'Subject: {self.code}'

    def get_lbd_probability_cache_key(self):
        return f'{CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.code}'

    @staticmethod
    def get_subjects(organization, order_by=()):
        """
        Returns subjects according to the input attributes.

        :param organization: organization name of the subjects
        :type organization: str
        :param order_by: ordering of the subjects
        :type order_by: tuple, optional
        :return: fetched subjects
        :rtype: QuerySet
        """
        if order_by:
            return Subject.objects.filter(organization=organization).order_by(*order_by)
        else:
            return Subject.objects.filter(organization=organization)

    @staticmethod
    def get_subjects_filtered(organization, search_phrase, order_by=()):
        """
        Returns subjects according to the input attributes.

        :param organization: organization name of the subjects
        :type organization: str
        :param search_phrase: search phrase to filter the subjects
        :type search_phrase: str
        :param order_by: ordering of the subjects
        :type order_by: tuple, optional
        :return: fetched subjects
        :rtype: QuerySet
        """
        return Subject.get_subjects(organization, order_by=order_by).filter(code__contains=search_phrase)

    @staticmethod
    def get_subject(pk=None, code=None):
        """
        Returns the subject according to the input attributes.

        :param pk: primary key of the subject
        :type pk: uuid (database specific), optional
        :param code: code of the subject
        :type code: str, optional
        :return: fetched subject
        :rtype: Record
        """

        # Validate the input arguments
        if not any((pk, code)):
            raise ValueError(f'Not enough information to get a subject')

        # Return the subject
        else:
            if pk:
                return get_object_or_404(Subject, id=pk)
            else:
                return get_object_or_404(Subject, code=code)


class ExaminationSession(models.Model):
    """Class implementing examination session model"""

    class Meta:
        """Model meta information definition"""

        # Default ordering of the records
        ordering = ['session_number']

    # Define the predictor data sequence (sequence of models to ge the features from)
    PREDICTOR_DATA_SEQUENCE = getattr(settings, 'PREDICTOR_CONFIGURATION')['predictor_data_sequence']

    # Define the model schema
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    session_number = models.SmallIntegerField('session number')
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)

    def __str__(self):
        return f'{self.session_number}. session for subject: {self.subject.code}'

    def get_lbd_probability_cache_key(self):
        return f'{CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.subject.code}_session_{self.id}'

    def get_lbd_probability_cache_key_for_subject(self):
        return f'{CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.subject.code}'

    @staticmethod
    def get_sessions(subject, order_by=()):
        """
        Returns sessions according to the input attributes.

        :param subject: subject record
        :type subject: Record
        :param order_by: ordering of the sessions
        :type order_by: tuple, optional
        :return: fetched sessions
        :rtype: QuerySet
        """
        if order_by:
            return ExaminationSession.objects.filter(subject=subject).order_by(*order_by)
        else:
            return ExaminationSession.objects.filter(subject=subject)

    @staticmethod
    def get_session(pk=None, subject=None, subject_code=None, session_number=None):
        """
        Returns the session according to the input attributes.

        :param pk: primary key of the session
        :type pk: uuid (database specific), optional
        :param subject: subject record
        :type subject: Record, optional
        :param subject_code: subject code,
        :type subject_code: str, optional
        :param session_number: session number
        :type session_number: int, optional
        :return: fetched session
        :rtype: Record
        """

        # Validate the input arguments
        if not any((pk, all((any((subject, subject_code)), session_number)))):
            raise ValueError(f'Not enough information to get a session')

        # Return the session
        else:
            if pk:
                return get_object_or_404(ExaminationSession, id=pk)
            else:
                if subject:
                    return get_object_or_404(ExaminationSession, subject=subject, session_number=session_number)
                else:
                    subject = Subject.get_subject(code=subject_code)
                    session = ExaminationSession.get_session(subject=subject, session_number=session_number)
                    return session

    def get_features_for_prediction(self):
        """Gets the prediction features for a given examination session"""

        # Prepare the features and labels buffer buffer
        feature_labels = []
        feature_values = []

        # Get the features for all data types specified in the predictor configuration
        for label in self.PREDICTOR_DATA_SEQUENCE:

            # Get the model class from the data to model class mapping
            model, model_configuration = DATA_TO_MODEL_CLASS_MAPPING[label]

            # Get the model record (skip if there is not record yet)
            record = model.get_data(examination_session=self)
            if not record:
                continue

            # Get the features for the referenced record
            features = model.get_features_from_record(record)
            features = model.get_features_as_kwargs(features)

            # Accumulate the features and labels
            values = []
            labels = []

            for supported_feature in model_configuration.get_predictor_feature_names():
                if supported_feature in features:
                    values.append(features[supported_feature])
                    labels.append(supported_feature)
                else:
                    values.append(None)
                    labels.append(None)

            # Add the specific features and labels to the overall collection
            feature_values += values
            feature_labels += labels

        # Return the labels and features for prediction
        return feature_labels, numpy.array(feature_values, dtype=numpy.float)


class CommonExaminationSessionData(models.Model):
    """Base class for examination session data (structured and unstructured)"""

    class Meta:
        """Meta class definition"""
        abstract = True

    # Define the configuration instance
    CONFIGURATION = None

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

    # Define the model schema
    examination_session = models.OneToOneField('ExaminationSession', on_delete=models.CASCADE, primary_key=True)
    description = models.CharField('description', max_length=255, blank=True)

    def get_lbd_probability_cache_key_for_subject(self):
        return f'{CACHE_LBD_PROBABILITY_PREFIX}_subject_{self.examination_session.subject.code}'

    def get_lbd_probability_cache_key_for_session(self):
        return f'{CACHE_LBD_PROBABILITY_PREFIX}_' \
               f'subject_{self.examination_session.subject.code}_' \
               f'session_{self.examination_session.id}'

    @classmethod
    def get_features_from_record(cls, record, **kwargs):
        """
        Returns the features as a list of dicts from the input record.

        :param record: feature-based data record
        :type record: Record
        :return: feature-based data (feature labels, feature values)
        :rtype: list of dicts
        """
        return []

    @classmethod
    def get_features_as_kwargs(cls, features):
        """Returns the features as kwargs (dict to be unfolded)"""
        return {
            feature[cls.FEATURE_LABEL_FIELD]: feature[cls.FEATURE_VALUE_FIELD]
            for feature in features
        }

    @classmethod
    def get_configured_feature_names(cls):
        """Returns the configured feature names"""
        return cls.CONFIGURATION.feature_names()

    @classmethod
    def get_provided_feature_names(cls, features):
        """Returns the provided feature names"""
        return [feature[cls.FEATURE_LABEL_FIELD] for feature in features]

    @classmethod
    def _adjust_feature_label_for_presentation(cls, label=None):
        """Adjusts the feature label for presentation"""
        return label

    @classmethod
    def _adjust_feature_title_for_presentation(cls, title):
        """Adjusts the feature title for presentation"""
        if not title or title == cls.UNFILLED_FEATURE_TITLE_REAL:
            return cls.UNFILLED_FEATURE_TITLE_REPR
        else:
            return title

    @classmethod
    def _adjust_feature_value_for_presentation(cls, value):
        """Adjusts the feature value for presentation"""
        if not value or value == cls.UNFILLED_FEATURE_VALUE_REAL:
            return cls.UNFILLED_FEATURE_VALUE_REPR
        else:
            return value

    @classmethod
    def _adjust_feature_label_for_computation(cls, label):
        """Adjusts the feature label for computation"""
        return label

    @classmethod
    def _adjust_feature_value_for_computation(cls, value):
        """Adjusts the feature value for computation"""
        if isinstance(value, str) and value in cls.UNFILLED_FEATURE_VALUE_REPR:
            return cls.UNFILLED_FEATURE_VALUE_REAL
        else:
            return value

    @classmethod
    def prepare_presentable(cls, record=None, features=None, **kwargs):
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
        features = cls.get_features_from_record(record, **kwargs) if not features else features

        # Return the presentable features
        return [{
            cls.FEATURE_LABEL_FIELD: cls._adjust_feature_label_for_presentation(feature.get(cls.FEATURE_LABEL_FIELD)),
            cls.FEATURE_TITLE_FIELD: cls._adjust_feature_title_for_presentation(feature.get(cls.FEATURE_TITLE_FIELD)),
            cls.FEATURE_VALUE_FIELD: cls._adjust_feature_value_for_presentation(feature.get(cls.FEATURE_VALUE_FIELD))
            } for feature in features
        ]

    @classmethod
    def prepare_computable(cls, record=None, features=None):
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
        features = cls.get_features_from_record(record) if not features else features

        # Return the computable features
        return [{
            cls.FEATURE_LABEL_FIELD: cls._adjust_feature_label_for_computation(feature[cls.FEATURE_LABEL_FIELD]),
            cls.FEATURE_VALUE_FIELD: cls._adjust_feature_value_for_computation(feature[cls.FEATURE_VALUE_FIELD])
            } for feature in features
        ]

    @classmethod
    def prepare_downloadable(cls, response, record=None, features=None):
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
        features = cls.get_features_from_record(record) if not features else features

        # Prepare the CSV writer
        writer = csv.writer(response)

        # Write the header and the body
        writer.writerow([element.get(cls.FEATURE_LABEL_FIELD) for element in features])
        writer.writerow([element.get(cls.FEATURE_VALUE_FIELD) for element in features])

        # Return the response
        return response

    @classmethod
    def read_features_from_file(cls, file=None, path=None):
        """Returns the features from the input file or file path"""

        # Prepare the features
        features = []

        # Read the data (feature names and feature values themselves)
        if is_csv_file(file=file, path=path):
            features = read_features_from_csv(file=file, path=path)
        if is_excel_file(file=file, path=path):
            features = read_features_from_excel(file=file, path=path)

        # Handle the case when no features were read
        if not features:
            return []

        # Return the features
        return [
            {cls.FEATURE_LABEL_FIELD: label, cls.FEATURE_VALUE_FIELD: value}
            for label, value in features
            if label in cls.CONFIGURATION.get_feature_names()
        ]

    @classmethod
    def get_data(cls, pk=None, examination_session=None, subject_code=None, session_number=None):
        """
        Returns the data according to the input attributes.

        Use-cases:
         1. get_data(pk)
            reads the record using its primary key
         2. get_data(examination_session)
            reads data using the foreign key to its examination session
         3. get_data(subject_code, session_number)
            reads data using the subject code and the session number

        :param pk: primary key of the data
        :type pk: uuid (database specific), optional
        :param examination_session: session record
        :type examination_session: Record, optional
        :param subject_code: subject code,
        :type subject_code: str, optional
        :param session_number: session number
        :type session_number: int, optional
        :return: fetched data
        :rtype: Record
        """

        # Validate the input arguments
        if not any((pk, examination_session, all((subject_code, session_number)))):
            raise ValueError(f'Not enough information to get data')

        # Fetch the data
        if not any((pk, examination_session)):
            session = ExaminationSession.get_session(subject_code=subject_code, session_number=session_number)
            fetched = cls.objects.filter(examination_session=session)
        else:
            if pk:
                fetched = cls.objects.filter(id=pk)
            else:
                fetched = cls.objects.filter(examination_session=examination_session)

        # Return the data
        return fetched.last() if fetched else None


class CommonFeatureBasedData(CommonExaminationSessionData):
    """Base class for feature-based examination session data"""

    class Meta:
        """Meta class definition"""
        abstract = True

    # Define the model schema
    data = models.FileField('data', upload_to='data/', validators=[FileExtensionValidator(['csv', 'xls', 'xlsx'])])

    @classmethod
    def get_features_from_record(cls, record, **kwargs):
        """Returns the features from the input record"""
        return cls.read_features_from_file(path=record.data.path) if record else []


class CommonQuestionnaireBasedData(CommonExaminationSessionData):
    """Base class for questionnaire-based examination session data"""

    class Meta:
        """Meta class definition"""
        abstract = True

    # Define the maximum question name to be shown/used
    MAX_QUESTION_LENGTH_PRESENTABLE = 100
    MAX_QUESTION_LENGTH_COMPUTABLE = None

    @classmethod
    def _adjust_question_length(cls, question):
        if question and len(question) > cls.MAX_QUESTION_LENGTH_PRESENTABLE:
            question = f'{question[:cls.MAX_QUESTION_LENGTH_PRESENTABLE]}...'
        return question

    @classmethod
    def get_features_from_record(cls, record, **kwargs):
        """Returns the features from the input record"""

        # Handle no record situation
        if not record:
            return []

        # Get the questionnaire question names
        names = cls.CONFIGURATION.get_feature_names()

        # Return the features (names as labels)
        if kwargs.get('use_questions'):

            # Prepare the questions (long and adjusted version)
            questions = cls.CONFIGURATION.get_questions()
            questions = [(question, cls._adjust_question_length(question)) for question in questions]

            # Return the features
            return [{
                cls.FEATURE_LABEL_FIELD: question,
                cls.FEATURE_TITLE_FIELD: question_adjusted,
                cls.FEATURE_VALUE_FIELD: getattr(record, name)}
                for name, (question, question_adjusted) in zip(names, questions)
            ]

        # Return the features (questions as labels)
        else:
            return [{
                cls.FEATURE_LABEL_FIELD: name,
                cls.FEATURE_VALUE_FIELD: getattr(record, name)}
                for name in names
            ]

    @classmethod
    def get_features_from_form(cls, form):
        """Create the record from the input form"""

        # Read the features from the file in the form
        features = cls.read_features_from_file(file=form.cleaned_data['file'])
        features = cls.prepare_computable(features=features)

        # Return the features
        return features

    @classmethod
    def create_from_form(cls, form, **kwargs):
        """Create the record from the input form"""

        # Read the features from the file in the form
        features = cls.get_features_from_form(form)

        # Convert the features to kwargs and merge them with the input kwargs
        record_data = {**cls.get_features_as_kwargs(features), **kwargs}

        # Create the record
        cls.objects.create(**record_data)

    @classmethod
    def update_from_form(cls, form, record, **kwargs):
        """Updates the record from the input form"""

        # Read the features from the file in the form
        features = cls.get_features_from_form(form)

        # Convert the features to kwargs and merge them with the input kwargs
        record_data = {**cls.get_features_as_kwargs(features), **kwargs}

        # Update the record
        for field, value in record_data.items():
            setattr(record, field, value)

        # Save the record
        record.save()

        # Return the updated record
        return record


class DataAcoustic(CommonFeatureBasedData):
    """Class implementing acoustic data model"""

    # Define the configuration instance
    CONFIGURATION = DataAcousticConfiguration()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Acoustic data for subject: {subject} ({session}. session)'


class DataQuestionnaire(CommonQuestionnaireBasedData):
    """Class implementing questionnaire data model"""

    # Define the configuration instance
    CONFIGURATION = DataQuestionnaireConfiguration()

    # Define the questions
    QUESTIONS = CONFIGURATION.get_questions()

    # Define the options
    OPTIONS = CONFIGURATION.get_options()

    # Define the model schema
    q1 = models.PositiveSmallIntegerField(QUESTIONS[0], choices=OPTIONS[0], blank=True, null=True)
    q2 = models.PositiveSmallIntegerField(QUESTIONS[1], choices=OPTIONS[1], blank=True, null=True)
    q3 = models.PositiveSmallIntegerField(QUESTIONS[2], choices=OPTIONS[2], blank=True, null=True)
    q4 = models.PositiveSmallIntegerField(QUESTIONS[3], choices=OPTIONS[3], blank=True, null=True)
    q5 = models.PositiveSmallIntegerField(QUESTIONS[4], choices=OPTIONS[4], blank=True, null=True)

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Questionnaire data for subject: {subject} ({session}. session)'


# Connect the signals
post_save.connect(prepare_predictor_api_for_created_user, sender=User)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataAcoustic)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataQuestionnaire)
post_save.connect(invalidate_cached_lbd_prediction_for_subject, sender=Subject)


# Define the data to (model class, model configuration class) mapping
DATA_TO_MODEL_CLASS_MAPPING = {
    'data_questionnaire': (DataQuestionnaire, DataQuestionnaireConfiguration),
    'data_acoustic': (DataAcoustic, DataAcousticConfiguration)
}

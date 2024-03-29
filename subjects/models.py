import numpy
import random
import string
import uuid
import secrets
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.shortcuts import get_object_or_404
from predictor.preprocessors import preprocess_feature
from .models_cache import SubjectCache, ExaminationSessionCache
from .models_formatters import FeaturesFormatter, format_feature_data_type
from .models_configuration import (
    SubjectDataConfiguration,
    DataAcousticConfiguration,
    DataActigraphyConfiguration,
    DataHandwritingConfiguration,
    DataPsychologyConfiguration,
    DataTCSConfiguration,
    DataCEIConfiguration
)
from .models_signals import (
    prepare_predictor_api_for_created_user,
    update_last_examined_on_for_subject,
    invalidate_cached_lbd_prediction_for_session,
    invalidate_cached_lbd_prediction_for_subject
)
from .models_io import (
    is_csv_file,
    is_excel_file,
    read_features_from_csv,
    read_features_from_excel
)


class User(AbstractUser):
    """Class implementing user model"""

    # Define the predictor ID generator
    PREDICTOR_ID_GENERATOR = uuid.uuid4

    # Define the predictor API attributes
    PREDICTOR_PASSWORD_LENGTH = 29

    # Define the model schema
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    predictor_username = models.CharField('predictor username', max_length=50, null=True, blank=True)
    predictor_password = models.CharField('predictor password', max_length=50, null=True, blank=True)
    predictor_registered = models.BooleanField('predictor registered', default=False)
    predictor_access_token = models.CharField('predictor access token', max_length=300, null=True, blank=True)
    predictor_refresh_token = models.CharField('predictor refresh token', max_length=300, null=True, blank=True)
    power_user = models.BooleanField('power user status', default=False)

    def get_predictor_authentication_credentials(self):
        """Returns the authentication credentials for the user instance"""
        return {'username': self.predictor_username, 'password': self.predictor_password}

    def get_predictor_access_token(self):
        """Returns the access token for the user instance"""
        return self.predictor_access_token

    def get_predictor_refresh_token(self):
        """Returns the refresh token for the user instance"""
        return self.predictor_refresh_token

    @classmethod
    def generate_predictor_username(cls):
        """Generates the predictor username"""
        return str(cls.PREDICTOR_ID_GENERATOR())

    @classmethod
    def generate_predictor_password(cls):
        """Generates the predictor username"""
        return secrets.token_urlsafe(cls.PREDICTOR_PASSWORD_LENGTH) + \
            ''.join(random.SystemRandom().choice(string.ascii_uppercase) for _ in range(1)) + \
            ''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(1)) + \
            ''.join(random.SystemRandom().choice(string.digits) for _ in range(1))


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

    # Define the configuration object
    CONFIGURATION = SubjectDataConfiguration

    # Define the cached data object
    CACHED_DATA = SubjectCache

    # Define the sex options for each subject
    SEX = [('M', 'Male'), ('F', 'Female')]

    # Define the model schema
    organization = models.ForeignKey('organization', on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField('subject code', max_length=50, unique=True)
    year_of_birth = models.SmallIntegerField('year of birth', null=True, blank=True)
    sex = models.CharField('sex', max_length=1, choices=SEX, null=True, blank=True)
    created_on = models.DateTimeField('created on', auto_now_add=True)
    updated_on = models.DateTimeField('updated on', auto_now=True)
    last_examined_on = models.DateTimeField('last examined on', null=True, blank=True)
    lbd_probability = models.FloatField('lbd_probability', null=True, blank=True)

    def __str__(self):
        return f'Subject: {self.code}'

    def get_lbd_probability_cache_key(self):
        return self.CACHED_DATA(self).get_lbd_probability_cache_key()

    @classmethod
    def get_features_from_record(cls, record):
        """Returns the features from the input record"""

        # Handle no record situation
        if not record:
            return []

        # Get the questionnaire question names
        names = cls.CONFIGURATION.get_available_feature_names()

        # Return the features
        return [{
            FeaturesFormatter.FEATURE_LABEL_FIELD: name,
            FeaturesFormatter.FEATURE_VALUE_FIELD: getattr(record, name)
            } for name in names
        ]

    def get_features_for_prediction(self):
        """Gets the prediction features for a given subject"""

        # Get the features for the referenced record
        features = self.get_features_from_record(self)
        features = FeaturesFormatter.get_features_as_kwargs(features)

        # Accumulate the features and labels
        feature_values = []
        feature_labels = []

        for supported_feature in self.CONFIGURATION.get_predictor_feature_names():
            if supported_feature in features:

                # Preprocess the feature
                label, value = preprocess_feature(features[supported_feature], supported_feature, model=self)

                # Accumulate the feature
                feature_values += value
                feature_labels += label

        # Return the labels and features for prediction
        return feature_labels, numpy.array(feature_values, dtype=float)

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
    PREDICTOR_DATA_SEQUENCE = getattr(settings, 'PREDICTOR_CONFIGURATION')['session_data_sequence']
    EXAMINATION_DATA_SEQUENCE = getattr(settings, 'DATA_CONFIGURATION')['data_sequence']

    # Define the cached data object
    CACHED_DATA = ExaminationSessionCache

    # Define the model schema
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='examination_sessions')
    session_number = models.SmallIntegerField('session number')
    internal_prefix = models.CharField('internal prefix', max_length=50, null=True, blank=True)
    created_on = models.DateTimeField('created on', auto_now_add=True)
    updated_on = models.DateTimeField('updated on', auto_now=True)
    examined_on = models.DateTimeField('examined on', null=True, blank=True)

    def __str__(self):
        return f'{self.session_number}. session for subject: {self.subject.code}'

    def get_lbd_probability_cache_key(self):
        return self.CACHED_DATA(self).get_lbd_probability_cache_key()

    def get_features_for_prediction(self):
        """Gets the prediction features for a given examination session"""

        # Prepare the features and labels buffer
        feature_labels = []
        feature_values = []

        # Get the features for all data types specified in the predictor configuration
        for label in self.PREDICTOR_DATA_SEQUENCE:

            # Get the model class from the data to model class mapping
            model = DATA_TO_MODEL_CLASS_MAPPING[label]

            # Get the model record (skip if there is no record yet)
            record = model.get_data(examination_session=self)
            if not record:
                continue

            # Get the features for the referenced record
            features = model.get_features_from_record(record)
            features = FeaturesFormatter.get_features_as_kwargs(features)

            # Accumulate the features and labels
            values = []
            labels = []

            for supported_feature in model.CONFIGURATION.get_predictor_feature_names():
                if supported_feature in features:

                    # Preprocess the feature
                    label, value = preprocess_feature(features[supported_feature], supported_feature, model=model)

                    # Accumulate the feature
                    values += value
                    labels += label

            # Add the specific features and labels to the overall collection
            feature_values += values
            feature_labels += labels

        # Return the labels and features for prediction
        return feature_labels, numpy.array(feature_values, dtype=float)

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


class CommonExaminationSessionData(models.Model):
    """Base class for examination session data (structured and unstructured)"""

    class Meta:
        """Meta class definition"""
        abstract = True

    # Define the configuration object
    CONFIGURATION = None

    # Define the model schema
    examination_session = models.OneToOneField('ExaminationSession', on_delete=models.CASCADE, primary_key=True)

    @classmethod
    def get_features_from_record(cls, record, **kwargs):
        """Returns the features as a list of dicts from the input record"""
        return []

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

        # Get the supported feature names
        supported_features = cls.CONFIGURATION.get_available_feature_names()

        # Get the features filter only for the supported ones and handle the data types)
        response = [
            {
                FeaturesFormatter.FEATURE_LABEL_FIELD: label,
                FeaturesFormatter.FEATURE_VALUE_FIELD: format_feature_data_type(
                    feature=value,
                    configuration=cls.CONFIGURATION.database.get('features_description', {}).get(label)
                )
            }
            for label, value in features
            if label in supported_features
        ]

        # Sort the features by the feature names
        response = sorted(response, key=lambda x: x[FeaturesFormatter.FEATURE_LABEL_FIELD])

        # Return the features
        return response

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


class DataAcoustic(CommonFeatureBasedData):
    """Class implementing acoustic data model"""

    # Define the configuration object
    CONFIGURATION = DataAcousticConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Acoustic data for subject: {subject} ({session}. session)'


class DataActigraphy(CommonFeatureBasedData):
    """Class implementing actigraphy data model"""

    # Define the configuration object
    CONFIGURATION = DataActigraphyConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Actigraphy data for subject: {subject} ({session}. session)'


class DataHandwriting(CommonFeatureBasedData):
    """Class implementing handwriting data model"""

    # Define the configuration object
    CONFIGURATION = DataHandwritingConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Handwriting data for subject: {subject} ({session}. session)'


class DataPsychology(CommonFeatureBasedData):
    """Class implementing psychology data model"""

    # Define the configuration object
    CONFIGURATION = DataPsychologyConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'Psychology data for subject: {subject} ({session}. session)'


class DataTCS(CommonFeatureBasedData):
    """Class implementing TCS data model"""

    # Define the configuration object
    CONFIGURATION = DataTCSConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'TCS data for subject: {subject} ({session}. session)'


class DataCEI(CommonFeatureBasedData):
    """Class implementing CEI data model"""

    # Define the configuration object
    CONFIGURATION = DataCEIConfiguration

    # Define the features description
    FEATURES_DESCRIPTION = CONFIGURATION.get_features_description()

    def __str__(self):
        subject = self.examination_session.subject.code
        session = self.examination_session.session_number
        return f'CEI data for subject: {subject} ({session}. session)'


# Connect the signals
post_save.connect(prepare_predictor_api_for_created_user, sender=User)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataAcoustic)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataActigraphy)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataHandwriting)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataPsychology)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataTCS)
post_save.connect(invalidate_cached_lbd_prediction_for_session, sender=DataCEI)
post_save.connect(invalidate_cached_lbd_prediction_for_subject, sender=Subject)
post_save.connect(update_last_examined_on_for_subject, sender=ExaminationSession)


# Define the data to the model class mapping
DATA_TO_MODEL_CLASS_MAPPING = {
    'acoustic': DataAcoustic,
    'actigraphy': DataActigraphy,
    'handwriting': DataHandwriting,
    'psychology': DataPsychology,
    'tcs': DataTCS,
    'cei': DataCEI
}


# Define the examination session parts
# 1. examination name
# 2. path name
# 3. model
examinations = [
    ('acoustic', 'session_detail_data_acoustic', DataAcoustic),
    ('actigraphy', 'session_detail_data_actigraphy', DataActigraphy),
    ('handwriting', 'session_detail_data_handwriting', DataHandwriting),
    ('psychology', 'session_detail_data_psychology', DataPsychology),
    ('tcs', 'session_detail_data_tcs', DataTCS),
    ('cei', 'session_detail_data_cei', DataCEI)
]

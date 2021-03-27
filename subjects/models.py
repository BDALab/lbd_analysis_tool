import csv
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.shortcuts import get_object_or_404


class User(AbstractUser):
    """Class implementing user model"""

    # Define the model schema
    organization = models.OneToOneField('Organization', on_delete=models.CASCADE, null=True, blank=True)


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
    description = models.CharField('description', max_length=255, blank=True)

    def __str__(self):
        return f'Subject: {self.code}'

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
            raise ValueError(f"Not enough information to get a subject")

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

    # Define the model schema
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    session_number = models.SmallIntegerField('session number')
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)

    def __str__(self):
        return f'{self.session_number}. session for subject: {self.subject.code}'

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
            raise ValueError(f"Not enough information to get a session")

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

    # Define the model schema
    examination_session = models.OneToOneField('ExaminationSession', on_delete=models.CASCADE)
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)

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
            raise ValueError(f"Not enough information to get data")

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

    @staticmethod
    def read_file(record):
        """
        Reads the feature-based data from the provided database records.

        :param record: feature-based data record
        :type record: Record
        :return: feature-based data (feature labels, feature values)
        :rtype: list of dicts
        """

        # Prepare the data
        feature_labels = []
        feature_values = []

        # Read the data (feature names and feature values themselves)
        with open(record.data.path, 'r') as csv_file:
            for i, row in enumerate(csv.reader(csv_file, delimiter=','), 1):
                if i == 1:
                    feature_labels = row
                if i == 2:
                    feature_values = row

        # Process the data and prepare the features
        features = [
            {'label': label, 'value': value}
            for label, value in zip(feature_labels, feature_values)
        ]

        # Return the features
        return features

    @classmethod
    def prepare_downloadable(cls, record, response):
        """
        Prepares the feature-based data to be downloaded.

        :param record: feature-based data record
        :type record: Record
        :param response: response to be filled with the feature-based data
        :type response: HttpResponse
        :return: response with the inserted data
        :rtype: HttpResponse
        """

        # Prepare the CSV writer
        writer = csv.writer(response)

        # Read the data
        data = cls.read_file(record)

        # Write the header and the body
        writer.writerow([element.get('label') for element in data])
        writer.writerow([element.get('value') for element in data])

        # Return the response
        return response


class DataAcoustic(CommonFeatureBasedData):
    """Class implementing acoustic data model"""

    # Define the model schema
    data = models.FileField('data', upload_to='data/', validators=[FileExtensionValidator(['csv'])])

    def __str__(self):
        return f'Acoustic data for {self.examination_session.session_number}. session'


class CommonQuestionnaireBasedData(CommonExaminationSessionData):
    """Base class for questionnaire-based examination session data"""

    class Meta:
        """Meta class definition"""
        abstract = True

    # Define the questions
    QUESTIONS = []

    # Define the questions statements
    QUESTIONS_STATEMENTS = {}

    def get_questions(self):
        return [
            {'question': self.QUESTIONS_STATEMENTS.get(question, question), 'answer': getattr(self, question)}
            for question in self.QUESTIONS
        ]

    @classmethod
    def prepare_downloadable(cls, record, response):
        """
        Prepares the questionnaire-based data to be downloaded.

        :param record: questionnaire-based data record
        :type record: Record
        :param response: response to be filled with the questionnaire-based data
        :type response: HttpResponse
        :return: response with the inserted data
        :rtype: HttpResponse
        """

        # Prepare the CSV writer
        writer = csv.writer(response)

        # Read the data
        data = cls.get_questions(record)

        # Write the header and the body
        writer.writerow([element.get('question') for element in data])
        writer.writerow([element.get('answer') for element in data])

        # Return the response
        return response


class DataQuestionnaire(CommonQuestionnaireBasedData):
    """Class implementing questionnaire data model"""

    # Define the questions
    QUESTIONS = ['q1', 'q2', 'q3', 'q4', 'q5']

    # Define the questions statements
    QUESTIONS_STATEMENTS = {
        'q1': 'question 1',
        'q2': 'question 2',
        'q3': 'question 3',
        'q4': 'question 4',
        'q5': 'question 5'
    }

    # Define the questionnaire data options
    Q1_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q2_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q3_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q4_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q5_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]

    # Define the model schema
    q1 = models.PositiveSmallIntegerField('question 1', choices=Q1_OPTIONS, blank=True, null=True)
    q2 = models.PositiveSmallIntegerField('question 2', choices=Q2_OPTIONS, blank=True, null=True)
    q3 = models.PositiveSmallIntegerField('question 3', choices=Q3_OPTIONS, blank=True, null=True)
    q4 = models.PositiveSmallIntegerField('question 4', choices=Q4_OPTIONS, blank=True, null=True)
    q5 = models.PositiveSmallIntegerField('question 5', choices=Q5_OPTIONS, blank=True, null=True)

    def __str__(self):
        return f'Questionnaire data for {self.examination_session.session_number}. session'

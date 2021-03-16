import csv
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser


# ------ #
# Models #
# ------ #

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


class ExaminationSession(models.Model):
    """Class implementing examination session model"""

    # Define the model schema
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    session_number = models.SmallIntegerField('session number')
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)

    def __str__(self):
        return f'{self.session_number}. session for subject: {self.subject.code}'


class DataAcoustic(models.Model):
    """Class implementing acoustic data model"""

    # Define the model schema
    examination_session = models.ForeignKey('ExaminationSession', on_delete=models.CASCADE)
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)
    data = models.FileField('data', upload_to='data/', validators=[FileExtensionValidator(['csv'])])

    def __str__(self):
        return f'Acoustic data for {self.examination_session.session_number}. session'

    @staticmethod
    def read_file(records):
        """
        Reads the acoustic data from the provided database records.

        :param records: acoustic data records
        :type records: query set
        :return: acoustic data (feature labels, feature values)
        :rtype: list of dicts
        """

        # Prepare the acoustic data
        feature_labels = []
        feature_values = []

        # Read the acoustic data (feature names and feature values themselves)
        with open(records.last().data.path, 'r') as csv_file:
            for i, row in enumerate(csv.reader(csv_file, delimiter=','), 1):
                if i == 1:
                    feature_labels = row
                if i == 2:
                    feature_values = row

        # Process the acoustic data
        acoustic_data = [
            {'label': label, 'value': value}
            for label, value in zip(feature_labels, feature_values)
        ]

        # Return the acoustic data
        return acoustic_data


class DataQuestionnaire(models.Model):
    """Class implementing questionnaire data model"""

    # Define the questions
    QUESTIONS = {
        "q1": "question 1",
        "q2": "question 2",
        "q3": "question 3",
        "q4": "question 4",
        "q5": "question 5"
    }

    # Define the questionnaire data options
    Q1_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q2_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q3_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q4_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]
    Q5_OPTIONS = [(1, 'A'), (2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')]

    # Define the model schema
    examination_session = models.ForeignKey('ExaminationSession', on_delete=models.CASCADE)
    description = models.CharField('description', max_length=255, blank=True)
    created_on = models.DateField('created on', auto_now_add=True)
    updated_on = models.DateField('updated on', auto_now=True)
    q1 = models.PositiveSmallIntegerField('question 1', choices=Q1_OPTIONS, blank=True, null=True)
    q2 = models.PositiveSmallIntegerField('question 2', choices=Q2_OPTIONS, blank=True, null=True)
    q3 = models.PositiveSmallIntegerField('question 3', choices=Q3_OPTIONS, blank=True, null=True)
    q4 = models.PositiveSmallIntegerField('question 4', choices=Q4_OPTIONS, blank=True, null=True)
    q5 = models.PositiveSmallIntegerField('question 5', choices=Q5_OPTIONS, blank=True, null=True)

    def __str__(self):
        return f'Questionnaire data for {self.examination_session.session_number}. session'

    @property
    def question_1(self):
        return {"question": self.QUESTIONS["q1"], "answer": self.q1}

    @property
    def question_2(self):
        return {"question": self.QUESTIONS["q2"], "answer": self.q2}

    @property
    def question_3(self):
        return {"question": self.QUESTIONS["q3"], "answer": self.q3}

    @property
    def question_4(self):
        return {"question": self.QUESTIONS["q4"], "answer": self.q4}

    @property
    def question_5(self):
        return {"question": self.QUESTIONS["q5"], "answer": self.q5}

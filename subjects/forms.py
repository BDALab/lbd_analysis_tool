from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Subject, DataAcoustic, DataQuestionnaire


# Get the user model
User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Class implementing custom user creation form"""

    class Meta:
        """Form definition"""

        # Database model
        model = User

        # Database model fields to be used in the form
        fields = ('username', 'email')

        # Database model field classes to be associated
        field_classes = {'username': UsernameField}


class SubjectModelForm(forms.ModelForm):
    """Class implementing subject form"""

    class Meta:
        """Form definition"""

        # Database model
        model = Subject

        # Database model fields to be used in the form
        fields = ('code', 'age', 'sex', 'nationality', 'description')


class DataAcousticForm(forms.ModelForm):
    """Class implementing acoustic data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataAcoustic

        # Database model fields to be used in the form
        fields = ('data', )


class DataQuestionnaireForm(forms.ModelForm):
    """Class implementing questionnaire data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataQuestionnaire

        # Database model fields to be used in the form
        fields = ('q1', 'q2', 'q3', 'q4', 'q5', 'description')


class UploadFileForm(forms.Form):
    """Class implementing uploading data form"""

    # Database model fields to be used in the form
    file = forms.FileField()

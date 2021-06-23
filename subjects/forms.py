from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Subject, DataAcoustic, DataQuestionnaire


# Get the Django-based user model
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
        fields = tuple(Subject.CONFIGURATION.get_form_fields())


class DataAcousticForm(forms.ModelForm):
    """Class implementing acoustic data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataAcoustic

        # Database model fields to be used in the form
        fields = tuple(DataAcoustic.CONFIGURATION.get_form_fields())


class DataQuestionnaireForm(forms.ModelForm):
    """Class implementing questionnaire data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataQuestionnaire

        # Database model fields to be used in the form
        fields = tuple(DataQuestionnaire.CONFIGURATION.get_form_fields())


class UploadFileForm(forms.Form):
    """Class implementing uploading data form"""

    # Database model fields to be used in the form
    file = forms.FileField()

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import (
    Subject,
    DataAcoustic,
    DataActigraphy,
    DataHandwriting,
    DataPsychology,
    DataTCS,
    DataCEI
)


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


class DataActigraphyForm(forms.ModelForm):
    """Class implementing actigraphy data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataActigraphy

        # Database model fields to be used in the form
        fields = tuple(DataActigraphy.CONFIGURATION.get_form_fields())


class DataHandwritingForm(forms.ModelForm):
    """Class implementing handwriting data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataHandwriting

        # Database model fields to be used in the form
        fields = tuple(DataHandwriting.CONFIGURATION.get_form_fields())


class DataPsychologyForm(forms.ModelForm):
    """Class implementing psychology data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataPsychology

        # Database model fields to be used in the form
        fields = tuple(DataPsychology.CONFIGURATION.get_form_fields())


class DataTCSForm(forms.ModelForm):
    """Class implementing TCS data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataTCS

        # Database model fields to be used in the form
        fields = tuple(DataTCS.CONFIGURATION.get_form_fields())


class DataCEIForm(forms.ModelForm):
    """Class implementing CEI data form"""

    class Meta:
        """Form definition"""

        # Database model
        model = DataCEI

        # Database model fields to be used in the form
        fields = tuple(DataCEI.CONFIGURATION.get_form_fields())


class UploadFileForm(forms.Form):
    """Class implementing uploading data form"""

    # Database model fields to be used in the form
    file = forms.FileField()

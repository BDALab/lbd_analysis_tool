import pandas
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from .models import Subject, ExaminationSession, DATA_TO_MODEL_CLASS_MAPPING
from .models_formatters import FeaturesFormatter
from .models_io import is_csv_file, is_excel_file, read_subjects_from_csv, read_subjects_from_excel


def import_session_data(subject, session_data):
    """
    Imports the session from the data provided from the external source.

    :param subject: subject record
    :type subject: Subject instance
    :param session_data: data for the session (columns + one data row)
    :type session_data: pandas.DataFrame
    :return: None
    :rtype: None type
    """

    # Get the available information in the provided session data
    available_information = session_data.columns

    # Validate the input attributes
    if 'session_number' not in available_information:
        return

    # Prepare the fields
    fields = {'session_number': session_data['session_number'].values[0]}

    # Create/update the examination session
    try:
        session = ExaminationSession.objects.get(subject=subject, session_number=fields['session_number'])
        setattr(session, 'subject', subject)
        setattr(session, 'session_number', fields['session_number'])
    except ObjectDoesNotExist:
        session = ExaminationSession(subject=subject, session_number=fields['session_number'])

    # Save the session instance
    session.save()

    # Create/update the examination session data
    for label in ExaminationSession.EXAMINATION_DATA_SEQUENCE:

        # Get the model class from the data to model class mapping
        model = DATA_TO_MODEL_CLASS_MAPPING[label]

        # Prepare the field
        fields = {
            feature: session_data[feature].values[0] if feature in available_information else None
            for feature in model.CONFIGURATION.get_available_feature_names()
        }

        # Get the features from the session data
        features = [{
            FeaturesFormatter.FEATURE_LABEL_FIELD: feature,
            FeaturesFormatter.FEATURE_VALUE_FIELD: fields[feature]}
            for feature in model.CONFIGURATION.get_available_feature_names()
        ]

        # Adjust the features
        features = FeaturesFormatter(model).prepare_computable(features=features)
        features = FeaturesFormatter.get_features_as_kwargs(features)

        # Prepare the features for the serialized/non-serialized features
        field, value = None, None
        if model.CONFIGURATION.serialized_features:
            field = model.CONFIGURATION.data_field
            value = ContentFile(pandas.DataFrame([features]).to_csv(index=False, line_terminator='\r'), 'features.csv')

        # Create/update the examination session data
        try:
            data = model.objects.get(examination_session=session)
            if model.CONFIGURATION.serialized_features:
                setattr(data, field, value)
            else:
                for feature_label, feature_value in features.items():
                    setattr(data, feature_label, feature_value)

        except ObjectDoesNotExist:
            if model.CONFIGURATION.serialized_features:
                data = model(examination_session=session, **{field: value})
            else:
                data = model(examination_session=session, **features)

        # Save the data instance
        data.save()


def import_sessions_data(user, sessions_data):
    """
    Imports the sessions from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param sessions_data: data for the sessions (columns + 1-N data row(s))
    :type sessions_data: pandas.DataFrame
    :return: None
    :rtype: None type
    """

    # Get the available information in the provided sessions data
    available_information = sessions_data.columns

    # Validate the input attributes
    if 'code' not in available_information or 'session_number' not in available_information:
        return

    # Prepare the fields
    fields = {
        'code': sessions_data['code'].values[0],
        'age': sessions_data['age'].values[0],
        'sex': sessions_data['sex'].values[0],
        'nationality': sessions_data['nationality'].values[0]
    }

    # Create/update the subject
    try:
        subject = Subject.objects.get(code=fields['code'])
        setattr(subject, 'age', fields['age'])
        setattr(subject, 'sex', fields['sex'])
        setattr(subject, 'nationality', fields['nationality'])
    except ObjectDoesNotExist:
        subject = Subject(organization=user.organization, **fields)

    # Save the subject instance
    subject.save()

    # Import the sessions
    for session_number, session_data in sessions_data.groupby('session_number'):
        import_session_data(subject, session_data)


def import_subject_data(user, subject_data):
    """
    Imports the subject from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param subject_data: data for the subject (columns + 1-N data row(s))
    :type subject_data: pandas.DataFrame
    :return: None
    :rtype: None type
    """
    for session_number, sessions_data in subject_data.groupby('session_number'):
        import_sessions_data(user, sessions_data)


def import_subjects_data(user, subjects_data):
    """
    Imports the subjects from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param subjects_data: data for the subjects (columns + 1-N data row(s))
    :type subjects_data: pandas.DataFrame
    :return: None
    :rtype: None type
    """
    for code, sessions_data in subjects_data.groupby('code'):
        import_subject_data(user, sessions_data)


def import_subjects_from_external_source(user, form):
    """Imports the subjects with the data from the external file"""

    # Get the file from the uploaded form
    file = form.cleaned_data['file']
    data = None

    # Read the data from the file
    if file:
        if is_csv_file(file=file):
            data = read_subjects_from_csv(file=file)
        if is_excel_file(file=file):
            data = read_subjects_from_excel(file=file)

    # Import the subjects with the data (examination sessions and data)
    if not data.empty:
        import_subjects_data(user, data)

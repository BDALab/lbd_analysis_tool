import pandas
from itertools import chain
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.conf import settings
from .models import Subject, ExaminationSession, DATA_TO_MODEL_CLASS_MAPPING
from .models_formatters import FeaturesFormatter
from .models_io import open_excel_file
from .views_io_utils import parse_sex, parse_year, parse_date


# Import configuration
import_configuration = getattr(settings, 'IMPORT_CONFIGURATION')


def import_session_data(user, subject, session_number, session_prefix, identity_data, features_data):
    """
    Imports the session from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param subject: subject
    :type subject: Subject instance
    :param session_number: session number
    :type session_number: int
    :param session_prefix: session prefix
    :type session_prefix: str
    :param identity_data: data for the identity of the subjects
    :type identity_data: pandas.Series
    :param features_data: data for the examination sessions and features of the subjects
    :type features_data: dict with pandas.Series
    :return: None
    :rtype: None type
    """

    # Create/update the examination session
    try:
        session = ExaminationSession.objects.get(subject=subject, session_number=session_number)
        setattr(session, 'subject', subject)
        setattr(session, 'session_number', session_number)
    except ObjectDoesNotExist:
        session = ExaminationSession(subject=subject, session_number=session_number)

    # Update the examination's internal prefix
    session.internal_prefix = session_prefix

    # Update the examination's timestamp
    field_name = f'{session_prefix} {import_configuration["date_of_examination"]}'
    field_data = identity_data[field_name] if field_name in identity_data.index else None
    session.examined_on = parse_date(field_data)

    # Save the session instance
    session.save()

    # Create/update the examination session data
    for label in ExaminationSession.EXAMINATION_DATA_SEQUENCE:

        # Get the pandas.DataFrame with the features for the given examination session
        s = features_data[label]
        s = {feature: s.loc[feature] for feature in s.index if feature.startswith(session_prefix)}

        # Get the available features
        available_features = s.keys()

        # Get the model class from the data to model class mapping
        model = DATA_TO_MODEL_CLASS_MAPPING[label]

        # Get features to import (add the examination session prefix)
        features_to_import = [
            f'{session_prefix} {feature}'
            for feature in model.CONFIGURATION.get_available_feature_names()
        ]

        # Prepare the fields
        fields = {
            feature: s[feature] if feature in available_features else None
            for feature in features_to_import
        }

        # Get the features from the session data
        features = [{
            FeaturesFormatter.FEATURE_LABEL_FIELD: feature.replace(session_prefix, '').strip(),
            FeaturesFormatter.FEATURE_VALUE_FIELD: fields[feature]}
            for feature in features_to_import
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


def import_sessions_data(user, subject, identity_data, features_data):
    """
    Imports the sessions from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param subject: subject
    :type subject: Subject instance
    :param identity_data: data for the identity of the subjects
    :type identity_data: pandas.Series
    :param features_data: data for the examination sessions and features of the subjects
    :type features_data: dict with pandas.Series
    :return: None
    :rtype: None type
    """

    # Get the subject feature names
    feature_names = list(set(chain.from_iterable(s.dropna().index.tolist() for s in features_data.values())))

    # Get the session information (before session and normal sessions)
    before_sessions = import_configuration.get('before_sessions', [])
    normal_sessions = import_configuration.get('normal_sessions', [])
    if not any((before_sessions, normal_sessions)):
        return

    # Prepare the session iterator
    session_iterator = []

    # Fill the session iterator
    for s in before_sessions:
        if any(True if c.startswith(s) else False for c in feature_names):
            session_iterator.append(s)
    for s in normal_sessions:
        if any(True if c.startswith(s) else False for c in feature_names):
            session_iterator.append(s)

    # Import the sessions
    for session_number, session_prefix in enumerate(session_iterator, 1):
        import_session_data(user, subject, session_number, session_prefix, identity_data, features_data)


def import_subject_data(user, subject_code, df_identity, df_features):
    """
    Imports the subject from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param subject_code: code of the subject
    :type subject_code: str
    :param df_identity: data for the identity of the subjects
    :type df_identity: pandas.DataFrame
    :param df_features: data for the examination sessions and features of the subjects
    :type df_features: dict with pandas.Dataframes
    :return: None
    :rtype: None type
    """

    # Get the subject's data
    identity_data = df_identity.loc[subject_code]
    features_data = {
        k: (v.loc[subject_code] if subject_code in v.index else pandas.Series([]))
        for k, v in df_features.items()
    }

    # Prepare the fields
    fields = {
        'code': subject_code,
        'sex': parse_sex(identity_data['Sex']),
        'year_of_birth': parse_year(identity_data['Date of birth'])
    }

    # Create/update the subject
    try:
        subject = Subject.objects.get(code=fields['code'])
        setattr(subject, 'year_of_birth', fields['year_of_birth'])
        setattr(subject, 'sex', fields['sex'])
    except ObjectDoesNotExist:
        subject = Subject(organization=user.organization, **fields)

    # Save the subject instance
    subject.save()

    # Import the sessions
    import_sessions_data(user, subject, identity_data, features_data)


def import_subjects_data(user, df_identity, df_features):
    """
    Imports the subjects from the data provided from the external source.

    :param user: logged-in user
    :type user: User instance
    :param df_identity: data for the identity of the subjects
    :type df_identity: pandas.DataFrame
    :param df_features: data for the examination sessions and features of the subjects
    :type df_features: dict with pandas.Dataframes
    :return: None
    :rtype: None type
    """

    # Get the list of subjects
    subjects = list(set(code for code in df_identity.index if code and isinstance(code, str)))

    # Import the sessions for every subject
    for code in subjects:
        import_subject_data(user, code, df_identity, df_features)


def import_subjects_from_external_source(user, form):
    """Imports the subjects with the data from the external file"""

    # Get the file from the uploaded form
    file = form.cleaned_data['file']

    with open_excel_file(file=file, path=None) as f:

        # Read the identities of the subjects
        try:
            df_identity = pandas.read_excel(
                io=f,
                sheet_name=import_configuration['identity_sheet'],
                index_col=import_configuration['index_column'],
                skiprows=import_configuration['skip_rows'])
        except ValueError:
            return

        # Prepare the dict of pandas.DataFrames for features
        df_features = {}

        # Read the examination sessions and features
        for feature_sheet in import_configuration['feature_sheets']:
            try:
                data = pandas.read_excel(
                    io=f,
                    sheet_name=feature_sheet,
                    index_col=import_configuration['index_column'],
                    skiprows=import_configuration['skip_rows'])
            except ValueError:
                continue

            if not data.empty:
                df_features[import_configuration['feature_sheets_mapping'][feature_sheet]] = data

        # Import the subjects with the data (examination sessions and data)
        if df_features:
            import_subjects_data(user, df_identity, df_features)

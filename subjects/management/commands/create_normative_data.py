import json
import numpy as np
from pprint import pprint
from datetime import datetime
from collections import defaultdict
from django.conf import settings
from django.core.management.base import BaseCommand
from subjects.models_formatters import FeaturesFormatter
from subjects.models import Subject, Organization, ExaminationSession, DATA_TO_MODEL_CLASS_MAPPING


# Set the organization to get the normative data for
organization = Organization.objects.get(name='fnusa')

# Set the debugging mode
debug = True


class Command(BaseCommand):
    help = 'Creates normative data from healthy subjects'

    def handle(self, *args, **kwargs):
        """Handles the command: creates normative data from healthy subjects"""

        t1 = datetime.now()
        print(f'Start: {t1}')

        # Get the configuration of the features
        features_config = getattr(settings, 'DATA_CONFIGURATION', {})['data']['session']

        # Get the healthy subjects
        healthy_subjects = Subject.get_subjects_filtered(organization=organization, search_phrase='HC')

        # Prepare the features buffer
        features_buffer = []

        # Fill the features buffer
        for i, subject in enumerate(healthy_subjects, 1):
            for session in ExaminationSession.get_sessions(subject):
                session_data = {}

                for modality_type, modality_model in DATA_TO_MODEL_CLASS_MAPPING.items():
                    session_data[modality_type] = {}

                    config = features_config[modality_type]['features_description']

                    data = modality_model.get_data(examination_session=session)
                    data = data if data else {}
                    if not data:
                        continue

                    features = FeaturesFormatter(modality_model).prepare_computable(record=data)
                    features = [
                        feature for feature in features
                        if config[feature[FeaturesFormatter.FEATURE_LABEL_FIELD]].get('type') == 'numerical'
                    ]

                    for feature in features:
                        label = feature[FeaturesFormatter.FEATURE_LABEL_FIELD]
                        value = feature[FeaturesFormatter.FEATURE_VALUE_FIELD]
                        session_data[modality_type][label] = value

                features_buffer.append(session_data)

        # --

        # Prepare the normative data buffer
        norms_buffer = {
            modality_type: defaultdict(list)
            for modality_type, _ in DATA_TO_MODEL_CLASS_MAPPING.items()
        }

        # Fill the normative data buffer
        for modality_type, _ in DATA_TO_MODEL_CLASS_MAPPING.items():
            for element in features_buffer:
                for feature_name, feature_value in element[modality_type].items():
                    norms_buffer[modality_type][feature_name].append(feature_value)

        # --

        # Prepare the normative data
        norms = {}

        # Compute the normative data
        for modality_type, modality_features in norms_buffer.items():
            norms[modality_type] = {}

            for feature_label, feature_values in modality_features.items():
                values = np.array([x for x in feature_values if x is not None])

                norms[modality_type][feature_label] = {
                    'median': round(float(np.median(values)), 6) if values.any() else None,
                    'iqr': round(float(np.subtract(*np.percentile(values, [75, 25]))), 6) if values.any() else None
                }

        # --

        # Store the normative data as a *.json file
        with open('normative.json', 'wt', encoding='utf-8') as f:
            json.dump(norms, f)

        pprint(norms)

        t2 = datetime.now()
        print(f'End: {str(t2)}')
        print(f'Time difference: {str(t2 - t1)}')

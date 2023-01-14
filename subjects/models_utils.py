import sys
from django.conf import settings
from subjects.models_formatters import FeaturesFormatter


# Presentation settings
presentation_config = getattr(settings, 'PRESENTATION_CONFIGURATION')['features']


def rename_feature(feature_label, feature_configuration):
    """Renames the feature according to the input configuration"""
    if feature_label not in feature_configuration:
        return feature_label
    if not feature_configuration[feature_label].get('name'):
        return feature_label
    return feature_configuration[feature_label]['name']


def compute_difference_from_norm(session_data, norm_data, modality):
    """Computes the difference between the features and the norm of a given modality (in a given session)"""

    # Prepare the modality presentation
    modality_presentation = presentation_config[modality]

    # Prepare the comparison
    comparison = []

    # Compute the comparison
    for data in session_data:
        orig = data[FeaturesFormatter.FEATURE_VALUE_FIELD]
        norm = norm_data[data[FeaturesFormatter.FEATURE_LABEL_FIELD]]['median'] \
            if data[FeaturesFormatter.FEATURE_LABEL_FIELD] in norm_data \
            else None

        orig = orig if orig is not None else None
        norm = norm if norm is not None else None

        comparison.append({
            'feature': rename_feature(data[FeaturesFormatter.FEATURE_LABEL_FIELD], modality_presentation),
            'difference': abs(((orig / (norm + sys.float_info.epsilon)) * 100) - 100) if all((orig, norm)) else None,
            'orig value': orig,
            'norm value': norm
        })

    # Return the comparison
    return comparison

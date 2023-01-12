def rename_feature(feature_label, feature_configuration):
    """Renames the feature according to the input configuration"""
    if feature_label not in feature_configuration:
        return feature_label
    if not feature_configuration[feature_label].get('name'):
        return feature_label
    return feature_configuration[feature_label]['name']

import pandas as pd
import plotly.express as px
from itertools import chain
from plotly.offline import plot
from django.conf import settings
from subjects.models_utils import rename_feature, compute_difference_from_norm


# Presentation settings
presentation_config = getattr(settings, 'PRESENTATION_CONFIGURATION')['features']


def visualize_most_differentiating_features(session_data, norm_data, modality, top_n=10):
    """Gets the visualization of the most differentiating features of a given modality (in a given session)"""

    # Prepare the comparison of the features to the norm
    comparison = compute_difference_from_norm(session_data, norm_data)
    comparison = [c for c in comparison if c['orig value'] and c['norm value']]

    # Prepare the modality presentation
    modality_presentation = presentation_config[modality]

    # Get the most discriminating features
    comparison = list(sorted(comparison, key=lambda x: x['difference'], reverse=True))
    comparison = comparison[:top_n] if top_n < len(comparison) else comparison

    # Prepare the data to be shown
    data = list(chain.from_iterable([
        [
            {
                'feature label': rename_feature(c['feature'], modality_presentation),
                'feature value': c['norm value'],
                'type': 'norm',
                'difference': c['difference']
            },
            {
                'feature label': rename_feature(c['feature'], modality_presentation),
                'feature value': c['orig value'],
                'type': 'subject',
                'difference': c['difference']
            }
        ]
        for c in comparison
    ]))

    if not data:
        return ''

    # Resort the data once again
    data = list(sorted(data, key=lambda x: x['difference'], reverse=True))

    # Prepare the graph
    fig = px.histogram(
        data_frame=pd.DataFrame(data),
        x='feature label',
        y='feature value',
        color='type',
        barmode='group'
    )
    fig.update_layout(
        title='Most differentiating features from the normative data',
        title_x=0.5,
        xaxis_title=None,
        yaxis_title='feature value'
    )

    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')

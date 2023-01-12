import pandas as pd
import plotly.express as px
from itertools import chain
from plotly.offline import plot
from subjects.models_formatters import FeaturesFormatter


def visualize_most_differentiating_features(session_data, norm_data, top_n=10):
    """Gets the visualization of the most differentiating features of a given modality (ina given session)"""

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

        if orig is not None and norm is not None:
            comparison.append({
                'feature': data[FeaturesFormatter.FEATURE_LABEL_FIELD],
                'difference': orig - norm,
                'orig value': orig,
                'norm value': norm
            })

    # Get the most discriminating features
    comparison = sorted(comparison, key=lambda x: x['difference'], reverse=True)
    comparison = comparison[:top_n] if top_n < len(comparison) else comparison

    # Prepare the data to be shown
    data = list(chain.from_iterable([
        [
            {
                'feature label': c['feature'],
                'feature value': c['norm value'],
                'type': 'norm'
            },
            {
                'feature label': c['feature'],
                'feature value': c['orig value'],
                'type': 'subject'
            }
        ]
        for c in comparison
    ]))

    if not data:
        return ''

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
        xaxis_title=None,
        yaxis_title='feature value'
    )
    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')

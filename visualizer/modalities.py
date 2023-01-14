import os
import secrets
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.offline import plot
from itertools import chain
from django.conf import settings
from subjects.models_utils import compute_difference_from_norm


def get_most_differentiating_features_graph(session_data, norm_data, modality, top_n=10):
    """Gets the most differentiating features of a given modality (in a given session)"""

    # Prepare the comparison of the features to the norm
    comparison = compute_difference_from_norm(session_data, norm_data, modality)
    comparison = [c for c in comparison if c['orig value'] and c['norm value']]

    # Get the most discriminating features
    comparison = list(sorted(comparison, key=lambda x: x['difference'], reverse=True))
    comparison = comparison[:top_n] if top_n < len(comparison) else comparison

    # Prepare the comparison
    comparison = list(chain.from_iterable([
        [
            {
                'feature label': c['feature'],
                'feature value': c['orig value'],
                'difference': c['difference'],
                'type': 'subject'
            },
            {
                'feature label': c['feature'],
                'feature value': c['norm value'],
                'difference': c['difference'],
                'type': 'norm'
            }
        ]
        for c in comparison
    ]))

    # Resort the data once again
    comparison = list(sorted(comparison, key=lambda x: x['difference'], reverse=True))

    if not comparison:
        return None

    # Prepare the graph
    fig = px.histogram(
        data_frame=pd.DataFrame(comparison),
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

    # Return the prepared graph object
    return fig


def visualize_most_differentiating_features(session_data, norm_data, modality, top_n=10):
    """Gets the visualization of the most differentiating features of a given modality (in a given session)"""

    # Get the most differentiating features of a given modality (in a given session)
    fig = get_most_differentiating_features_graph(session_data, norm_data, modality, top_n)

    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='') if fig else ''


def save_most_differentiating_features(session_data, norm_data, modality, top_n=10):
    """Saves the most differentiating features of a given modality (in a given session)"""

    # Get the most differentiating features of a given modality (in a given session)
    fig = get_most_differentiating_features_graph(session_data, norm_data, modality, top_n)
    if not fig:
        return ''

    # Get the path to save the graph into
    save_path = os.path.join(getattr(settings, 'TEMP_PATH'), f'{modality}-{secrets.token_urlsafe(16)}.png')

    # Save the prepared graph
    fig.write_image(save_path)

    # Return the path to the saved graph
    return save_path


def get_most_differentiating_features_graph_and_table(session_data, norm_data, modality, top_n=10):
    """Gets the most differentiating features of a given modality (in a given session)"""

    # Prepare the comparison of the features to the norm
    comparison = compute_difference_from_norm(session_data, norm_data, modality)
    comparison = [c for c in comparison if c['orig value'] and c['norm value']]

    # Get the most discriminating features
    comparison = list(sorted(comparison, key=lambda x: x['difference'], reverse=True))
    comparison = comparison[:top_n] if top_n < len(comparison) else comparison

    # work only features with a reasonable data
    comparison = [c for c in comparison if c['orig value'] and c['norm value'] and c['difference']]
    if not comparison:
        return None

    features_labels = [c['feature'] for c in comparison]

    # Add the table data
    table_head = ['feature label', 'value (subject)', 'value (norm)', 'difference [%]']
    table_rows = [
        [
            c['feature'] if len(c['feature']) < 15 else f'{c["feature"][:15]}...',
            '{:.4f}'.format(c['orig value']),
            '{:.4f}'.format(c['norm value']),
            '{:.4f}'.format(c['difference'])
        ]
        for c in comparison
    ]
    table_data = [table_head, *table_rows]

    # Create a table
    fig = ff.create_table(table_data, height_constant=60)

    # Prepare the comparison for the graph
    comparison = list(chain.from_iterable([
        [
            {
                'feature label': c['feature'],
                'feature value': c['norm value'],
                'difference': c['difference'],
                'type': 'norm'
            },
            {
                'feature label': c['feature'],
                'feature value': c['orig value'],
                'difference': c['difference'],
                'type': 'subject'
            }
        ]
        for c in comparison
    ]))

    # Resort the data once again
    comparison = list(sorted(comparison, key=lambda x: x['difference'], reverse=True))

    # Add the graph data
    norm = [c['feature value'] for c in comparison if c['type'] == 'norm']
    orig = [c['feature value'] for c in comparison if c['type'] == 'subject']

    # Make traces for graph
    trace_norm = go.Bar(
        x=features_labels,
        y=norm,
        xaxis='x2',
        yaxis='y2',
        marker=dict(color='#ef553b'),
        name='norm'
    )
    trace_orig = go.Bar(
        x=features_labels,
        y=orig,
        xaxis='x2',
        yaxis='y2',
        marker=dict(color='#6366f1'),
        name='subject'
    )

    # Add trace data to figure
    fig.add_traces([trace_orig, trace_norm])

    # initialize x-axis2 and y-axis2
    fig['layout']['xaxis2'] = {}
    fig['layout']['yaxis2'] = {}

    # Edit layout for subplots
    fig.layout.yaxis.update({'domain': [0, .45]})
    fig.layout.yaxis2.update({'domain': [.6, 1]})

    # The graph's y-axis2 MUST BE anchored to the graph's x-axis2 and vice versa
    fig.layout.yaxis2.update({'anchor': 'x2'})
    fig.layout.xaxis2.update({'anchor': 'y2'})
    fig.layout.yaxis2.update({'title': 'feature value'})

    # Update the margins to add a title and see graph x-labels.
    fig.layout.margin.update({'t': 75, 'l': 50})
    fig.layout.update({'title': 'Most differentiating features from the normative data'})

    # Update the height because adding a graph vertically will interact with
    # the plot height calculated for the table
    fig.layout.update({'height': 800, 'title_x': 0.5})

    # Return the prepared graph object
    return fig


def visualize_most_differentiating_features_and_table(session_data, norm_data, modality, top_n=10):
    """Gets the visualization of the most differentiating features of a given modality (in a given session)"""

    # Get the most differentiating features of a given modality (in a given session)
    fig = get_most_differentiating_features_graph_and_table(session_data, norm_data, modality, top_n)

    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='') if fig else ''


def save_most_differentiating_features_and_table(session_data, norm_data, modality, top_n=10):
    """Saves the most differentiating features of a given modality (in a given session)"""

    # Get the most differentiating features of a given modality (in a given session)
    fig = get_most_differentiating_features_graph_and_table(session_data, norm_data, modality, top_n)
    if not fig:
        return ''

    # Get the path to save the graph into
    save_path = os.path.join(getattr(settings, 'TEMP_PATH'), f'{modality}-{secrets.token_urlsafe(16)}.png')

    # Save the prepared graph
    fig.write_image(save_path)

    # Return the path to the saved graph
    return save_path

import os
import secrets
import pandas as pd
import plotly.express as px
from plotly.offline import plot
from django.conf import settings
from subjects.models import ExaminationSession
from subjects.views_predictors import ExaminationSessionLBDPredictor


def compute_evolution_of_predictions(user, subject):
    """Computes the evolution of preDLB of a subject"""

    # Compute the predicted probabilities (per session)
    probabilities = [
        {
            'examination session': s.session_number,
            'preDLB probability': ExaminationSessionLBDPredictor.predict_lbd_probability(user, s)
        }
        for s in ExaminationSession.objects.filter(subject=subject)
    ]

    # Return the predicted probabilities
    return probabilities


def get_evolution_of_predictions_graph(user, subject):
    """Gets the evolution of preDLB of a subject"""

    # Prepare the predicted probabilities (per session)
    probabilities = compute_evolution_of_predictions(user, subject)
    if not probabilities:
        return None

    # Prepare the graph
    fig = px.bar(
        data_frame=pd.DataFrame(probabilities),
        x='examination session',
        y='preDLB probability',
        text='preDLB probability',
    )
    fig.update_layout(
        title='Evolution of preDLB probability',
        title_x=0.5,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, len(probabilities) + 1)),
            ticktext=list(range(1, len(probabilities) + 1))
        )
    )
    fig.update_traces(marker_color='#6366f1')

    # Return the prepared graph object
    return fig


def visualize_evolution_of_predictions(user, subject):
    """Gets the visualization of the evolution of preDLB of a subject"""

    # Get the evolution of preDLB of a subject
    fig = get_evolution_of_predictions_graph(user, subject)

    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='') if fig else ''


def save_evolution_of_predictions(user, subject):
    """Saves the evolution of preDLB of a subject"""

    # Get the evolution of preDLB of a subject
    fig = get_evolution_of_predictions_graph(user, subject)
    if not fig:
        return ''

    # Get the path to save the graph into
    save_path = os.path.join(getattr(settings, 'TEMP_PATH'), f'{subject.code}-{secrets.token_urlsafe(16)}.png')

    # Save the prepared graph
    fig.write_image(save_path)

    # Return the path to the saved graph
    return save_path

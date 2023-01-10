import pandas as pd
import plotly.express as px
from plotly.offline import plot
from subjects.models import ExaminationSession
from subjects.views_predictors import ExaminationSessionLBDPredictor


def get_visualization_of_evolution_of_predictions(user, subject):
    """Gets the visualization of the evolution of preDLB of a subject"""

    # Prepare the predicted probabilities (per session)
    probabilities = [
        {
            'examination session': s.session_number,
            'preDLB probability': ExaminationSessionLBDPredictor.predict_lbd_probability(user, s)
        }
        for s in ExaminationSession.objects.filter(subject=subject)
    ]

    # Prepare the graph
    fig = px.bar(
        data_frame=pd.DataFrame(probabilities),
        x='examination session',
        y='preDLB probability',
        text='preDLB probability',
    )
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, len(probabilities) + 1)),
            ticktext=list(range(1, len(probabilities) + 1))
        )
    )

    # Return the prepared graph object (as a DIV element)
    return plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text="")

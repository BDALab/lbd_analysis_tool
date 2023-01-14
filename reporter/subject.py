import os
from fpdf import FPDF
from datetime import datetime
from django.conf import settings
from visualizer.subject import save_evolution_of_predictions
from visualizer.modalities import save_most_differentiating_features_and_table
from subjects.models import examinations
from subjects.models_formatters import FeaturesFormatter
from subjects.views_predictors import SubjectLBDPredictor


class SubjectPDFReport(FPDF):
    """Class implementing a PDF report for subjects"""

    # Define the general cell height
    ch = 8

    def __init__(self):
        super().__init__()
        self.lbd_path = ''

    def header(self):
        self.set_font('Arial', '', 12)
        self.cell(0, 8, 'Subject preDLB diagnosis report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f'{self.page_no()}', 0, 0, 'C')

    def set_lbd_probability_graph(self, user, subject):
        self.lbd_path = save_evolution_of_predictions(user, subject)

    def get_lbd_probability_graph(self):
        if not self.lbd_path:
            return None
        with open(self.lbd_path, 'rb') as f:
            return f.read()


def create_report(request, subject):
    """Creates a PDF report"""

    # Create a subject PDF report
    pdf = SubjectPDFReport()

    # Predict the probability of preDLB for a subject
    if not subject.lbd_probability:
        subject.lbd_probability = SubjectLBDPredictor.predict_lbd_probability(request.user, subject)

    # --
    # First page: general information
    # --

    # Make a new page
    pdf.add_page()

    pdf.ln(pdf.ch)
    pdf.ln(pdf.ch)
    pdf.ln(pdf.ch)

    # Add the subject information
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(w=0, h=20, txt=subject.code, ln=1)

    pdf.set_font('Arial', '', 14)
    pdf.cell(w=60, h=pdf.ch, txt='Date: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(datetime.now().strftime('%d.%m.%Y, %H:%M:%S')), ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Organization: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=subject.organization.name, ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Number of examinations: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(subject.examination_sessions.count()), ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Probability of preDLB: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(subject.lbd_probability or ''), ln=1)

    # --
    # Second page: evolution of preDLB probability
    # --

    # Make a new page
    pdf.add_page()

    pdf.ln(pdf.ch)

    pdf.multi_cell(w=0, h=4, txt='Predicted probability of preDLB per examination session', align='C')

    pdf.ln(pdf.ch)

    # Add the predicted preDLB probabilities
    pdf.set_lbd_probability_graph(request.user, subject)
    if pdf.lbd_path:
        pdf.image(pdf.lbd_path, x=25, y=None, w=160, h=0, type='png', link='')

    # --
    # Other pages: most differentiating features
    # --

    # Get the last examination session
    last_session = subject.examination_sessions.last()
    if not last_session:
        return ''

    # Get the data per modality for the last examination session
    examination_data = [
        (modality, model, model.get_data(examination_session=last_session))
        for modality, _, model in examinations
    ]

    # Add the examination data on separate pages of the report
    for modality_label, modality_model, modality_data in examination_data:

        # Make a new page
        pdf.add_page()

        pdf.ln(pdf.ch)

        modality_txt = modality_label if modality_label not in ('cei', 'tcs') else modality_label.upper()
        pdf.multi_cell(w=0, h=4, txt=f'Most differentiation features for: {modality_txt} data', align='C')

        pdf.ln(pdf.ch)

        # Get the normative data for the modality
        norm_data = getattr(settings, 'NORM_CONFIGURATION')[modality_label]

        # Get the computation data
        if modality_data:
            comp_data = FeaturesFormatter(modality_model).prepare_computable(record=modality_data)
        else:
            comp_data = None

        # Add the most differentiating features for the modality
        if comp_data and norm_data:
            graph_path = save_most_differentiating_features_and_table(comp_data, norm_data, modality_label, top_n=10)
        else:
            graph_path = None

        if graph_path:
            pdf.image(graph_path, x=25, y=None, w=160, h=0, type='png', link='')
        else:
            for _ in range(15):
                pdf.ln(pdf.ch)
            pdf.multi_cell(w=0, h=4, txt='No data available for this modality', align='C')

    # --
    # Save the report
    # --

    # Prepare the filepath to store the report into
    output_path = os.path.join(getattr(settings, 'REPORTS_PATH'), f'{subject.code}.pdf')

    # Save the generated report
    pdf.output(output_path, 'F')

    # Return the path to the generated report
    return output_path

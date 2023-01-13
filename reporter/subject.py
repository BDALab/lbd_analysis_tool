import os
from fpdf import FPDF
from datetime import datetime
from django.conf import settings
from visualizer.subject import save_evolution_of_predictions
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
        with open(self.lbd_path, 'rb') as f:
            return f.read()


def create_report(request, subject):
    """Creates a PDF report"""

    # Create a subject PDF report
    pdf = SubjectPDFReport()

    # Predict the probability of preDLB for a subject
    if not subject.lbd_probability:
        subject.lbd_probability = SubjectLBDPredictor.predict_lbd_probability(request.user, subject)

    # Add the header information
    pdf.add_page()

    pdf.ln(pdf.ch)
    pdf.ln(pdf.ch)

    pdf.set_font('Arial', 'B', 18)
    pdf.cell(w=0, h=20, txt=subject.code, ln=1)

    pdf.set_font('Arial', '', 14)
    pdf.cell(w=60, h=pdf.ch, txt='Date: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(datetime.now().strftime("%d.%m.%Y, %H:%M:%S")), ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Organization: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=subject.organization.name, ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Number of examinations: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(subject.examination_sessions.count()), ln=1)
    pdf.cell(w=60, h=pdf.ch, txt='Probability of preDLB: ', ln=0)
    pdf.cell(w=60, h=pdf.ch, txt=str(subject.lbd_probability or ''), ln=1)

    pdf.ln(pdf.ch)

    # Add the predicted preDLB probabilities
    pdf.set_lbd_probability_graph(request.user, subject)
    pdf.image(pdf.lbd_path, x=25, y=None, w=160, h=0, type='png', link='')

    # Prepare the filepath to store the report into
    output_path = os.path.join(getattr(settings, 'REPORTS_PATH'), f'{subject.code}.pdf')

    # Save the generated report
    pdf.output(output_path, 'F')

    # Return the path to the generated report
    return output_path

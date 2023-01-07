import lorem
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF


# cell height
ch = 8


class PDF(FPDF):

    def __init__(self):
        super().__init__()

    def header(self):
        self.set_font('Arial', '', 12)
        self.cell(0, 8, 'Header', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'C')


if __name__ == '__main__':

    # Load or prepare pandas DataFrame
    df = pd.DataFrame({'feature 1': ['cat 1', 'cat 2', 'cat 3', 'cat 4'], 'feature 2': [400, 300, 200, 100]})

    # Save figures to use in the PDF
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    sns.barplot(data=df, x='feature 1', y='feature 2')
    plt.title("Chart")
    plt.savefig('./example_chart.png', transparent=False,  facecolor='white', bbox_inches="tight")
    plt.close()

    # Generate PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(w=0, h=20, txt="Title", ln=1)

    pdf.set_font('Arial', '', 16)
    pdf.cell(w=30, h=ch, txt="Date: ", ln=0)
    pdf.cell(w=30, h=ch, txt="01/01/2022", ln=1)
    pdf.cell(w=30, h=ch, txt="Author: ", ln=0)
    pdf.cell(w=30, h=ch, txt="Subject XYZ", ln=1)

    pdf.ln(ch)
    pdf.multi_cell(w=0, h=5, txt=lorem.paragraph())

    pdf.image('./example_chart.png', x=10, y=None, w=100, h=0, type='PNG', link='')

    pdf.ln(ch)
    pdf.multi_cell(w=0, h=5, txt=lorem.paragraph())

    pdf.ln(ch)

    # Table Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, ch, 'Feature 1', 1, 0, 'C')
    pdf.cell(40, ch, 'Feature 2', 1, 1, 'C')

    # Table contents
    pdf.set_font('Arial', '', 16)
    for i in range(0, len(df)):
        pdf.cell(40, ch, df['feature 1'].iloc[i], 1, 0, 'C')
        pdf.cell(40, ch, df['feature 2'].iloc[i].astype(str), 1, 1, 'C')

    pdf.output(f'./example.pdf', 'F')

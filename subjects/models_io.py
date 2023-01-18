import io
import csv
import openpyxl
from django.http import HttpResponse
from .models_formatters import FeaturesFormatter


# Define the file extensions
CSV_EXTENSIONS = ('.csv', )
XLS_EXTENSIONS = ('.xls', '.xlsx')


def export_data(request, code, session_number, model):
    """
    Exports the data in a CSV file that is downloaded in a browser.

    :param request: HTTP request
    :type request: Request
    :param code: code of the subject
    :type code: str
    :param session_number: session number
    :type session_number: str
    :param model: model to be used to get the data to be exported
    :type model: Model
    :return: HTTP response for the data to be exported
    :rtype: HttpResponse
    """

    # Prepare the HTTP response and the fetched data to be exported
    response = HttpResponse(content_type='text/csv')
    fetched = model.get_data(subject_code=code, session_number=session_number)

    # Prepare the fetched data to be downloadable
    response = FeaturesFormatter(model).prepare_downloadable(record=fetched, response=response)

    # Set the content disposition (to be downloaded by a browser)
    response['Content-Disposition'] = 'attachment; filename="exported.csv"'

    # Return the HTTP response
    return response


def export_report(request, report_path, subject_code, session_number=None):
    """
    Exports the report in a PDF file that is downloaded in a browser.

    :param request: HTTP request
    :type request: Request
    :param subject_code: code of the subject
    :type subject_code: str
    :param session_number: number of the examination session
    :type session_number: str
    :param report_path: path to the report to be exported
    :type report_path: str
    :return: HTTP response for the report to be exported
    :rtype: HttpResponse
    """

    # Prepare the HTTP response and the fetched data to be exported
    response = HttpResponse(content=open(report_path, 'rb'), content_type='application/pdf')

    # Prepare the file name for the attachment
    if session_number:
        file_name = f'report-{subject_code}_session_{session_number}.pdf'
    else:
        file_name = f'report-{subject_code}.pdf'

    # Set the content disposition (to be downloaded by a browser)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    # Return the HTTP response
    return response


def is_csv_file(file=None, path=None):
    """Returns if the input file/path is a *.CSV file"""
    if not any((file, path)):
        raise ValueError(f'Not enough arguments to decide about the file type')
    return get_file_name(file=file, path=path).endswith(CSV_EXTENSIONS)


def is_excel_file(file=None, path=None):
    """Returns if the input file/path is a *.XLS or *.XLSX file"""
    if not any((file, path)):
        raise ValueError(f'Not enough arguments to decide about the file type')
    return get_file_name(file=file, path=path).endswith(XLS_EXTENSIONS)


def read_features_from_csv(file=None, path=None):
    """Reads the features and labels from a *.CSV file"""

    # Validate the input arguments
    if not any((file, path)):
        raise ValueError(f'Not enough arguments to read from the *.csv file')

    with open_csv_file(file=file, path=path) as file:

        # Prepare the data
        feature_labels = []
        feature_values = []

        # Read the features and labels
        for i, row in enumerate(csv.reader(file, delimiter=','), 1):
            if i == 1:
                feature_labels = row
            if i == 2:
                feature_values = row

    # Return the features and labels
    return zip(feature_labels, feature_values)


def read_features_from_excel(file=None, path=None):
    """Reads the features and labels from a *.XLSX/*.XLS file"""

    # Validate the input arguments
    if not any((file, path)):
        raise ValueError(f'Not enough arguments to read from the *.xls/*.xlsx file')

    with open_excel_file(file=file, path=path) as file:

        # Read the workbook and the specific worksheet
        workbook = openpyxl.load_workbook(file)
        worksheet = workbook[workbook.worksheets[0].title]

        # Prepare the data
        feature_labels = []
        feature_values = []

        # Read the features and labels
        for i, row in enumerate(worksheet.iter_rows(), 1):
            if i == 1:
                feature_labels = [cell.value for cell in row]
            if i == 2:
                feature_values = [cell.value for cell in row]

    # Return the features and labels
    return zip(feature_labels, feature_values)


def get_file_name(file, path):
    return (file.name if file else path).lower().strip()


def open_csv_file(file, path):
    return io.StringIO(file.read().decode('utf-8')) if file else open(path, 'r')


def open_excel_file(file, path):
    return file if file else open(path, 'rb')

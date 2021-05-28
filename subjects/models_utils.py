import io
import csv


def is_csv_file(file):
    """Returns if the input file is a *.CSV file"""
    return file.name.lower().strip().endswith(".csv")


def is_excel_file(file):
    """Returns if the input file is a *.XLS or *.XLSX file"""
    return file.name.lower().strip().endswith((".xls", ".xlsx"))


def read_from_csv(file):
    """Reads the features and labels from a *.CSV file"""

    # Decode the Django InMemoryUploadedFile to be read by the reader
    file = io.StringIO(file.read().decode('utf-8'))

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


# TODO: @zolo add read_from_excel

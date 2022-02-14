import numpy
import pandas
import datetime
import dateutil.parser as date_parser


def parse_sex(element):
    """Parses the sex while supporting multiple types and formats"""
    return str(element) if element else None


def parse_year(element):
    """Parses the while supporting multiple types and formats"""

    # Handle various date formats and data types
    if isinstance(element, str):
        return int(date_parser.parse(element).year) if element else None
    if isinstance(element, int):
        return element
    if isinstance(element, datetime.datetime):
        try:
            return int(element.year)
        except ValueError:
            return None

    # Handle no date situation
    if not element or not numpy.isfinite(element):
        return None

    # Raise an exception for unsupported date
    raise TypeError(f"Unsupported date type for {element} ({type(element)})")


def parse_date(element):
    """Parses the date while supporting multiple types and formats"""

    # Handle various date formats and data types
    if isinstance(element, str):
        return date_parser.parse(element) if element else None
    if isinstance(element, datetime.datetime):
        return element if not isinstance(element, pandas._libs.tslibs.nattype.NaTType) else None

    # Handle no date situation
    if not element or not numpy.isfinite(element):
        return None

    # Raise an exception for unsupported date
    raise TypeError(f"Unsupported date type for {element} ({type(element)})")

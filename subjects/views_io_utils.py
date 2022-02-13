import numpy as np
import datetime
import dateutil.parser as date_parser
from itertools import chain


def parse_sex(element):
    """Parses the sex while supporting multiple types and formats"""
    return str(element) if element else None


def parse_year_of_birth(element):
    """Parses the year of birth while supporting multiple types and formats"""

    # Handle various date formats and data types
    if isinstance(element, str):
        return int(date_parser.parse(element).year)
    if isinstance(element, int):
        return element
    if isinstance(element, datetime.datetime):
        return int(element.year)

    # Handle no date situation
    if not element or not np.isfinite(element):
        return None

    # Raise an exception for unsupported date
    raise TypeError(f"Unsupported date type for {element} ({type(element)})")

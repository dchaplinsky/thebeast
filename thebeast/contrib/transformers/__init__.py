from typing import List
from dateutil.parser import parse as dt_parse  # type: ignore
from names_translator.name_utils import try_to_fix_mixed_charset, parse_and_generate  # type: ignore


# TODO: split into dates/names/others files


def mixed_charset_fixer(values: List[str]) -> List[str]:
    return [try_to_fix_mixed_charset(value) for value in values]


def anydate_parser(values: List[str]) -> List[str]:
    return [str(dt_parse(value).date()) for value in values]


def anydatetime_parser(values: List[str]) -> List[str]:
    return [str(dt_parse(value)) for value in values]


def incomplete_date_converter(value: str) -> str:
    """
    Transforms strings of the form \\w{2}.\\w{2}.\\w{4} to dates as strings, expressed in ISO-8601 format:
    There is no additional verification on digits.
    FTM comprehends date in mentioned format. If there are any inconsistencies, it will warn us.

        Parameters:
                value (str): Input string of the form \\w{2}.\\w{2}.\\w{4}

        Returns:
                formatted_date (str): Date as a string, expressed in ISO-8601 format

    """
    formatted_date = "-".join(elem if elem.isdigit() else "-" for elem in value.split(".")[::-1])
    return formatted_date


def iso_date_parser(values: List[str]) -> List[str]:
    return [incomplete_date_converter(value) for value in values]


def names_transliteration(values: List[str]) -> List[str]:
    result: List[str] = []

    for value in values:
        result += parse_and_generate(value)

    return result

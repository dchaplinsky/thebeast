from typing import List
from dateutil.parser import parse as dt_parse  # type: ignore

from names_translator.name_utils import try_to_fix_mixed_charset, parse_and_generate  # type: ignore
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy


# TODO: split into dates/names/others files


def trim_string(values: List[StrProxy], strip=" ") -> List[StrProxy]:
    """
    Strip garbage from string argument
    """
    return [value.inject_meta_to_str(value.strip(strip)) for value in values]


def mixed_charset_fixer(values: List[StrProxy]) -> List[StrProxy]:
    """
    Fix values where cyrillic symbols are replaced with similarly looking latin ones
    And vice versa
    """
    # TODO: add different locales in accordance to the way the str was fixed
    return [value.inject_meta_to_str(try_to_fix_mixed_charset(value)) for value in values]


def anydate_parser(values: List[StrProxy], **kwargs) -> List[StrProxy]:
    """
    Trying to parse date with dateutil lib
    """
    return [value.inject_meta_to_str(dt_parse(value, **kwargs).date()) for value in values]


def anydatetime_parser(values: List[StrProxy], **kwargs) -> List[StrProxy]:
    """
    Trying to parse datetime with dateutil lib
    """
    return [value.inject_meta_to_str(dt_parse(value, **kwargs)) for value in values]


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


def iso_date_parser(values: List[StrProxy]) -> List[StrProxy]:
    return [value.inject_meta_to_str(incomplete_date_converter(value)) for value in values]


def names_transliteration(values: List[StrProxy]) -> List[StrProxy]:
    result: List[StrProxy] = []

    for value in values:
        # TODO: add different locales in accordance to the transliteration scheme
        result += [value.inject_meta_to_str(v) for v in parse_and_generate(value)]

    return result

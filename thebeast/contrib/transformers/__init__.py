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


def names_transliteration(values: List[str]) -> List[str]:
    result: List[str] = []

    for value in values:
        result += parse_and_generate(value)

    return result

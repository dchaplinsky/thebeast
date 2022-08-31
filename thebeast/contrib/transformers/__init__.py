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


# Transforms strings of the form \w{2}.\w{2}.\w{4} to dates as strings, expressed in ISO-8601 format:
# xx.tt.ssss -> yyyy-mm-dd
# There is no additional verification on digits.
# ftm comprehends date in mentioned format. If there are any inconsistencies, it will warn us.
def date_parser_helper(value: str) -> str:
    to_return = []
    # iterate through components of string starting from the end
    for elem in value.split(".")[::-1]:
        # if elem contains digits, append to other components, else transform to "-"
        to_return.append(elem if str.isdigit(elem) else "-")
    return "-".join(to_return)


def iso_date_parser(values: List[str]) -> List[str]:
    if(len(values) > 1): print(values)
    return [date_parser_helper(value) for value in values]


def names_transliteration(values: List[str]) -> List[str]:
    result: List[str] = []

    for value in values:
        result += parse_and_generate(value)

    return result

from typing import List
from dateutil.parser import parse as dt_parse  # type: ignore
import datetime

from names_translator.name_utils import try_to_fix_mixed_charset, parse_and_generate  # type: ignore
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
import regex as re
import html


# TODO: split into dates/names/others files


def trim_string(values: List[StrProxy], strip=" ") -> List[StrProxy]:
    """
    Strip garbage from string argument
    """
    return [value.inject_meta_to_str(value.strip(strip)) for value in values]


def convert_case(values: List[StrProxy], case="upper") -> List[StrProxy]:
    """
    Converts string case
    """

    if case == "upper":
        return [value.inject_meta_to_str(value.upper()) for value in values]

    if case == "lower":
        return [value.inject_meta_to_str(value.lower()) for value in values]

    raise ValueError("Invalid case value, expecting 'upper' or 'lower'")


def mixed_charset_fixer(values: List[StrProxy]) -> List[StrProxy]:
    """
    Fix values where cyrillic symbols are replaced with similarly looking latin ones
    And vice versa
    """
    # TODO: add different locales in accordance to the way the str was fixed
    return [
        value.inject_meta_to_str(try_to_fix_mixed_charset(value)) for value in values
    ]


def anydate_parser(values: List[StrProxy], silent=False, **kwargs) -> List[StrProxy]:
    """
    Trying to parse date with dateutil lib
    """

    res = []

    for value in values:
        try:
            res.append(value.inject_meta_to_str(dt_parse(value, **kwargs).date()))
        except Exception:
            if silent:
                pass
            else:
                raise

    return res


def anydatetime_parser(values: List[StrProxy], **kwargs) -> List[StrProxy]:
    """
    Trying to parse datetime with dateutil lib
    """
    return [value.inject_meta_to_str(dt_parse(value, **kwargs)) for value in values]


def from_unixtime(
    values: List[StrProxy], silent=False, skip_zero_date=True
) -> List[StrProxy]:
    """
    Trying to create datetime from unix timestamp (utc)

    Args:
        values: list of unix timestamps as strings
        silent: if True, will not raise exceptions and just skip the value
        skip_zero_date: if True, will skip 0 unix timestamps
    Returns:
        list of datetime objects
    """

    res = []

    for value in values:
        try:
            if skip_zero_date and int(value) == 0:
                continue

            # This one was implemented incorrectly and was giving different naive datetimes
            # according to the timezone of the machine it was run on.
            # To keep the same behavior, we need to replace the timezone with UTC and
            # then remove tzinfo.
            res.append(
                value.inject_meta_to_str(
                    datetime.datetime.fromtimestamp(
                        int(value), tz=datetime.timezone.utc
                    ).replace(tzinfo=None)
                )
            )
        except Exception:
            if silent:
                pass
            else:
                raise

    return res


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
    formatted_date = "-".join(
        elem if elem.isdigit() else "-" for elem in value.split(".")[::-1]
    )
    return formatted_date


def iso_date_parser(values: List[StrProxy]) -> List[StrProxy]:
    return [
        value.inject_meta_to_str(incomplete_date_converter(value)) for value in values
    ]


def names_transliteration(values: List[StrProxy]) -> List[StrProxy]:
    result: List[StrProxy] = []

    for value in values:
        # TODO: add different locales in accordance to the transliteration scheme
        result += [value.inject_meta_to_str(v) for v in parse_and_generate(value)]

    return result


def do_normalize_email(value: str) -> str:
    """
    Normalizes email, stripping any plus and dot syntax from user name.

    For example:
        foo.bar@gmail.com => foobar@gmail.com
        foo+bar@gmail.com => foo@gmail.com
    """

    # if it's not a email - return it as is
    if not re.fullmatch(
        r"^[0-9a-z._+-]+\@[0-9a-z._+-]+\.[0-9a-z._+-]{2,}$", value, re.IGNORECASE
    ):
        return value

    name, domain = value.split("@", 1)
    # remove dots and/or +suffix from name
    name = re.sub("(\\.|\\+.+$)", "", name)
    return "@".join([name, domain]).lower()


def normalize_email(values: List[StrProxy]) -> List[StrProxy]:
    return [value.inject_meta_to_str(do_normalize_email(value)) for value in values]


def normalize_phone(values: List[StrProxy]) -> List[StrProxy]:
    """
    Normalizes phone number, prepending a plus symbol to it.
    This is needed because FtM expects phone to start with plus, and phones with just nmumbers will be skipepd.

    For example:
        79787458007 => +79787458007
    """
    return [
        value.inject_meta_to_str("+" + value) if not value.startswith("+") else value
        for value in values
    ]


def decode_html_entities(values: List[StrProxy]) -> List[StrProxy]:
    """
    Decode HTML entities
    """

    return [value.inject_meta_to_str(html.unescape(value)) for value in values]


def do_pad_string(value: str, length, pad_char=" ", align="left") -> str:
    if align == "left":
        return value.ljust(length, pad_char)
    elif align == "right":
        return value.rjust(length, pad_char)
    else:
        raise ValueError("Invalid align value, expecting left or right")


def pad_string(
    values: List[StrProxy], length, pad_char=" ", align="left"
) -> List[StrProxy]:
    """
    Pad string to desired length
    """

    return [
        value.inject_meta_to_str(do_pad_string(value, int(length), pad_char, align))
        for value in values
    ]

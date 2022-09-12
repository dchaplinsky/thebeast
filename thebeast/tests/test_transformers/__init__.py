from typing import Dict, List

import regex as re
from dateutil.parser import parse as dt_parse  # type: ignore


def mp_record_transformer(record: List[Dict]):
    """
    Test transformer that can be applied to the MPs dataset to extract the number of days
    that each deputy served during convocation
    """

    for r in record:
        date_from = dt_parse(re.findall(r"(\d{2}\.\d{2}\.\d{4})", r["date_from"])[0])
        date_to = dt_parse(re.findall(r"(\d{2}\.\d{2}\.\d{4})", r["date_to"])[0])

        r["days_served"] = (date_to - date_from).days

    return record

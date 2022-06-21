import sys
import json
from typing import Iterable
from followthemoney.schema import Schema  # type: ignore
import smart_open  # type: ignore


class FTMLinesWriter:
    """
    Class to write FTM jsonlines into any file-like object that smart_open supports
    or stdout (-)
    """

    def __init__(self, output_uri: str) -> None:
        if output_uri == "-":
            self.output = sys.stdout
        else:
            self.output = smart_open.open(output_uri)

    def write_entities(self, entities: Iterable[Schema], flush: bool=True) -> None:
        for entity in entities:
            self.output.write(json.dumps(entity.to_dict(), sort_keys=True) + "\n")

        if flush:
            self.output.flush()

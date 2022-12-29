import json
from typing import Iterable
from followthemoney.schema import Schema  # type: ignore

from .abstract import AbstractWriter


class FTMLinesWriter(AbstractWriter):
    """
    Class to write FTM jsonlines into any file-like object that smart_open supports
    or stdout (-)
    """

    def write_entities(self, entities: Iterable[Schema], flush: bool = True) -> None:
        for entity in entities:
            self.output.write(json.dumps(entity, sort_keys=True) + "\n")

        if flush:
            self.output.flush()

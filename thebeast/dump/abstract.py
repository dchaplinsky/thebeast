import sys
import smart_open  # type: ignore
from followthemoney.schema import Schema  # type: ignore

from typing import Iterable, List


class AbstractWriter:
    """
    Abstract class to write entities in a given format
    """

    def __init__(self, output_uri: str, meta_fields: List[str]) -> None:
        self.meta_fields: List[str] = meta_fields

        if output_uri == "-":
            self.output = sys.stdout
        else:
            self.output = smart_open.open(output_uri, "w")

    def write_entities(self, entities: Iterable[Schema], flush: bool = True) -> None:
        raise NotImplementedError("You have to redefine it")

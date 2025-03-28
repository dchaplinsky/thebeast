import json
from typing import Iterable
from thebeast.types import RedGreenEntity

from .abstract import AbstractWriter


class FTMLinesWriter(AbstractWriter):
    """
    Class to write FTM jsonlines into any file-like object that smart_open supports
    or stdout (-)
    """

    def write_entities(
        self, entities: Iterable[RedGreenEntity], flush: bool = True
    ) -> None:
        for entity in entities:
            line: str = (
                json.dumps(entity.payload, sort_keys=True, ensure_ascii=False) + "\n"
            )

            if entity.valid:
                self.output_fh.write(line)
            else:
                self.error_fh.write(line)

        if flush:
            self.output_fh.flush()
            if self.error_uri != self.output_uri:
                self.error_fh.flush()

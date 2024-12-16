import sys
import smart_open  # type: ignore
from thebeast.types import RedGreenEntity

from typing import Iterable, List, TextIO


class AbstractWriter:
    """
    Abstract class to write entities in a given format
    """

    def __init__(
        self, output_uri: str, meta_fields: List[str], error_uri: str = "/dev/null"
    ) -> None:
        """
        Error_uri (defaulted to /dev/null). By changing it you might route invalid entites
        to /dev/null, same file as valid ones or separate file for the debugging
        """

        self.meta_fields: List[str] = meta_fields
        self.output_uri: str = output_uri

        self.output_uri = self._resolve_uri(output_uri)
        self.error_uri = self._resolve_uri(error_uri)

        self.output_fh = self._get_filehandler(self.output_uri)
        if self.output_uri == self.error_uri:
            self.error_fh = self.output_fh
        else:
            self.error_fh = self._get_filehandler(self.error_uri)

    def _resolve_uri(self, uri: str) -> str:
        if uri in ["-", "/dev/stdout"]:
            return "/dev/stdout"
        elif uri in ["/dev/stderr"]:
            return "/dev/stderr"
        else:
            return uri

    def _get_filehandler(self, uri: str) -> TextIO:
        if uri == "/dev/stdout":
            return sys.stdout
        elif uri == "/dev/stderr":
            return sys.stderr
        else:
            return smart_open.open(uri, "w")

    def write_entities(
        self, entities: Iterable[RedGreenEntity], flush: bool = True
    ) -> None:
        raise NotImplementedError("You have to redefine it")

    def close(self):
        if self.output_uri not in ["/dev/stdout", "/dev/stderr"]:
            self.output_fh.close()

        if self.error_uri not in ["/dev/stdout", "/dev/stderr", self.output_uri]:
            self.error_fh.close()


class AbstractStatementsWriter(AbstractWriter):
    pass

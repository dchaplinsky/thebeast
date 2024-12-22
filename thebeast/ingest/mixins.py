from typing import Iterator, Generator, Dict, Union
from glob import iglob
import csv
import json

try:
    from ijson.backends import yajl2_c as ijson
except ImportError:
    from ijson.backends import yajl2_cffi as ijson


# Naming for mixing is simple. First part is the purpose
# Second part is the list of pipeline elements that it redefines


class GlobSourcerMixin:
    """
    Instead of reading just one file, load multiple files by a file mask
    """

    def sourcer(self):
        for fname in iglob(self.input_uri):
            yield fname


class CSVDictReaderMixin:
    """
    Read CSV with the header
    """

    def __init__(
        self,
        input_uri: str,
        delimiter: str = ",",
        quotechar: str = '"',
        lineterminator: str = "\r\n",
        doublequote: bool = True,
        escapechar: Union[str, None] = None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(input_uri, *args, **kwargs)

        self.dialect_params = {
            "delimiter": delimiter,
            "quotechar": quotechar,
            "lineterminator": lineterminator,
            "doublequote": doublequote,
            "escapechar": escapechar,
        }

    def reader(self, iterator: Iterator) -> Generator[Dict, None, None]:
        for line in csv.DictReader(iterator, **self.dialect_params):
            yield line


class TSVDictReaderMixin(CSVDictReaderMixin):
    """
    Read TSV with the header
    """

    def __init__(self, input_uri: str, *args, **kwargs) -> None:
        super().__init__(input_uri=input_uri, delimiter="\t", *args, **kwargs)


class JSONLinesReaderMixin:
    """
    Read jsonlines
    """

    def reader(self, iterator: Iterator) -> Generator[Dict, None, None]:
        for line in iterator:
            yield json.loads(line)


class JSONReaderMixin:
    """
    Read json arrays using ijson lib. Accepts an extra option to filter the content
    """

    def __init__(self, input_uri: str, ijson_prefix="item", *args, **kwargs):
        """
        ijson_prefix by default is set to item, which means
        'iterate top-level array found in the document'.
        You can override it to traverse dicts, nested arrays, etc.
        For more information on ijson prefix please visit https://pypi.org/project/ijson/#id17
        """
        super().__init__(input_uri, *args, **kwargs)
        self.ijson_prefix = ijson_prefix
        # ijson requires a binary file
        self.filemode = "rb"

    def reader(self, iterator: Iterator) -> Generator[Dict, None, None]:
        """
        Read json arrays using ijson lib. Accepts an extra option to filter the content
        """
        for line in ijson.items(iterator, self.ijson_prefix):
            yield line

from typing import Iterator, Generator, Dict
from glob import iglob
from csv import DictReader
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
    Read CSV/TSV with the header
    """
    def reader(self, iterator: Iterator)-> Generator[Dict, None, None]:
        for l in DictReader(iterator):
            yield l


class JSONLinesReaderMixin:
    """
    Read jsonlines
    """
    def reader(self, iterator: Iterator)-> Generator[Dict, None, None]:
        for l in iterator:
            yield json.loads(l)


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


    def reader(self, iterator: Iterator)-> Generator[Dict, None, None]:
        for l in ijson.items(iterator, self.ijson_prefix):
            yield l

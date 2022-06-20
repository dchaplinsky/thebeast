from .abstract import AbstractIngest
from .mixins import CSVDictReaderMixin, GlobSourcerMixin, JSONLinesReaderMixin, JSONReaderMixin


class CSVDictReader(CSVDictReaderMixin, AbstractIngest):
    """
    Class to ingest a single CSV file, provided with
    input_uri
    """

    pass


class CSVDictGlobReader(CSVDictReaderMixin, GlobSourcerMixin, AbstractIngest):
    """
    Class to load multiple CSV/TSV files by file mask
    """

    pass


class JSONLinesGlobReader(JSONLinesReaderMixin, GlobSourcerMixin, AbstractIngest):
    """
    Class to load multiple jsonlines files by file mask
    """

    pass



class JSONGlobReader(JSONReaderMixin, GlobSourcerMixin, AbstractIngest):
    """
    Class to load multiple json files by file mask with ijson stream reader
    """

    pass

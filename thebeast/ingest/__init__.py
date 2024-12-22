from .abstract import AbstractIngestor
from .mixins import (
    CSVDictReaderMixin,
    GlobSourcerMixin,
    JSONLinesReaderMixin,
    JSONReaderMixin,
    TSVDictReaderMixin,
)


class CSVDictReader(CSVDictReaderMixin, AbstractIngestor):
    """
    Class to ingest a single CSV file, provided with
    input_uri
    """

    pass


class CSVDictGlobReader(CSVDictReaderMixin, GlobSourcerMixin, AbstractIngestor):
    """
    Class to load multiple CSV files by file mask
    """

    pass


class TSVDictGlobReader(TSVDictReaderMixin, GlobSourcerMixin, AbstractIngestor):
    """
    Class to load multiple TSV files by file mask
    """

    pass


class JSONLinesGlobReader(JSONLinesReaderMixin, GlobSourcerMixin, AbstractIngestor):
    """
    Class to load multiple jsonlines files by file mask
    """

    pass


class JSONGlobReader(JSONReaderMixin, GlobSourcerMixin, AbstractIngestor):
    """
    Class to load multiple json files by file mask with ijson stream reader
    """

    pass


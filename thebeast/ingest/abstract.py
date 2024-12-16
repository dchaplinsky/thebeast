from typing import TextIO, Iterator, Union, Dict, Generator


import smart_open  # type: ignore
from thebeast.types import Record


class AbstractIngestor:
    """
    Abstract class for the data ingestion

    The general idea is to pass a mandatory input_uri
    (some of implementations might require more params)
    which will be turned into one or more file uri,
    each of which will be opened for reading and transformed
    into the one single iterator over dicts.

    You might want to redefine this method to validate and store
    more params (for example, credentials for a remote source)
    """

    def __init__(
        self, input_uri: str, input_encoding: str = "utf-8", *args, **kwargs
    ) -> None:
        self.input_uri = input_uri
        self.input_encoding = input_encoding
        self.filemode = "rt"

    def __iter__(self):
        return self.iterator()

    def sourcer(self) -> Generator[str, None, None]:
        """
        Converts input_uri and other optional params to the
        generator that yields file uris.
        This will allow to use the same ingestion logic to work
        with a single local file, glob-like URIs
        for files scattered over the FS, S3 bucket to iterate
        over files, etc, etc

        In it's most abstract implementation just returns
        the input_uri to work with a singular file

        You might want to redefine this method to turn and input_uri
        into the list of file uris, again, using glob lib, or reading
        the list of files on S3 bucket or even reading a files from an
        index or generating the remote file URIs according to some schema
        """
        yield self.input_uri

    def opener(self, file_uri: str) -> Union[TextIO, Iterator]:
        """
        Turns a file uri into the file-like handle using smart_open
        Important thing to notice: smart_open will cover decompression for you too

        You might want to redefine this method to support reading
        from an exotic sources not covered with smart_open.

        It might also return an iterator of a different kind, for example
        a cursor in mongodb or postgres. In this case reader will be very lean,
        basically converting each item into the dict
        """
        return smart_open.open(
            uri=file_uri, mode=self.filemode, encoding=self.input_encoding
        )

    def reader(self, iterator: Iterator) -> Generator[Dict, None, None]:
        """
        Iterates over the opened file handle (or any other iterator,
        for example a queryset) and yields dicts from it's content

        You definitely want to redefine this to turn the file content
        into the meaningful records (for example to open csv, json, xml etc)
        """
        raise NotImplementedError("You have to redefine it")

    def iterator(self) -> Generator[Record, None, None]:
        """
        Stitches all the things above together.

        You might want to redefine it for database collections
        """
        for file_uri in self.sourcer():
            with self.opener(file_uri) as fp:
                for i, record in enumerate(self.reader(fp)):
                    yield Record(payload=record, record_no=i, input_uri=file_uri)

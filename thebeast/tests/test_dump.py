import unittest
import sys
import json
from io import StringIO
from followthemoney import model as ftm  # type: ignore

from thebeast.dump import FTMLinesWriter


class CaptureStdout:
    def __enter__(self):
        self.out, sys.stdout = sys.stdout, StringIO()

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.out


class MappingDumpTests(unittest.TestCase):
    def test_empty_dump(self):
        with CaptureStdout():
            dumper = FTMLinesWriter("-", meta_fields=[])
            dumper.write_entities([], flush=True)

            sys.stdout.seek(0)
            self.assertEqual(sys.stdout.read(), "")

    def test_empty_entity_dump(self):
        with CaptureStdout():
            dumper = FTMLinesWriter("-", meta_fields=[])
            entity = ftm.make_entity("Person")
            dumper.write_entities([entity])

            sys.stdout.seek(0)
            self.assertEqual(json.loads(sys.stdout.read()), {"id": None, "properties": {}, "schema": "Person"})

    def test_full_entity_dump(self):
        with CaptureStdout():
            dumper = FTMLinesWriter("-", meta_fields=[])
            entity = ftm.make_entity("Person")
            entity.set("name", "")

            entity.set("name", "Ющенко Віктор Андрійович")
            entity.set("firstName", "Віктор")
            entity.set("lastName", "Ющенко")
            entity.set("fatherName", "Андрійович")
            entity.set("sourceUrl", "https://uk.wikipedia.org/wiki/Ющенко_Віктор_Андрійович")
            entity.set("wikipediaUrl", "https://uk.wikipedia.org/wiki/Ющенко_Віктор_Андрійович")
            entity.make_id(["foo", "bar"])

            dumper.write_entities([entity])

            sys.stdout.seek(0)
            self.assertEqual(
                json.loads(sys.stdout.read()),
                {
                    "id": "3c8082874130892b92381b7f5b1a4577a3334e28",
                    "properties": {
                        "fatherName": ["Андрійович"],
                        "firstName": ["Віктор"],
                        "lastName": ["Ющенко"],
                        "name": ["Ющенко Віктор Андрійович"],
                        "sourceUrl": ["https://uk.wikipedia.org/wiki/Ющенко_Віктор_Андрійович"],
                        "wikipediaUrl": ["https://uk.wikipedia.org/wiki/Ющенко_Віктор_Андрійович"],
                    },
                    "schema": "Person",
                },
            )

    # TODO: tests with real files

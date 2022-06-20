import unittest
from pathlib import Path
from thebeast.conf.mapping import SourceMapping
from thebeast.conf.exc import InvalidOverridesException, InvalidMappingException

class MappingReaderTests(unittest.TestCase):
    def test_valid_mapping(self):
        mapping = SourceMapping(Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"))
        items = list(mapping.ingestor)

        self.assertEqual(len(items), 983)
        self.assertEqual(
            set(items[0].keys()),
            {
                "name",
                "party",
                "district",
                "date_from",
                "date_to",
                "link",
            },
        )

    def test_valid_ingest_overrides(self):
        mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
            ingest_overrides={"input_uri": "thebeast/tests/sample/csv/rada4.tsv"})
        items = list(mapping.ingestor)

        self.assertEqual(len(items), 505)
        self.assertEqual(
            set(items[0].keys()),
            {
                "name",
                "party",
                "district",
                "date_from",
                "date_to",
                "link",
            },
        )

    def test_invalid_overrides(self):
        with self.assertRaises(InvalidOverridesException):
            mapping = SourceMapping(
                Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
                ingest_overrides={"input_uri": 1337})


    def test_invalid_mapping(self):
        with self.assertRaises(InvalidMappingException):
            mapping = SourceMapping(
                Path("thebeast/tests/sample/mappings/invalid.yaml"))

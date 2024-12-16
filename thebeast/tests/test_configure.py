import unittest
from pathlib import Path
from thebeast.conf.mapping import SourceMapping
from thebeast.conf.exc import InvalidOverridesException, InvalidMappingException


class MappingReaderTests(unittest.TestCase):
    def test_valid_mapping(self):
        mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml")
        )
        items = list(mapping.ingestor)

        self.assertEqual(len(items), 983)
        self.assertEqual(
            set(items[0].payload.keys()),
            {
                "name",
                "party",
                "district",
                "date_from",
                "date_to",
                "link",
            },
        )
        self.assertIsNotNone(mapping.ftm)

    def test_valid_ingest_overrides(self):
        mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
            ingest_overrides={"input_uri": "thebeast/tests/sample/csv/rada4.tsv"},
        )
        items = list(mapping.ingestor)

        self.assertEqual(len(items), 505)
        self.assertEqual(
            set(items[0].payload.keys()),
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
            SourceMapping(
                Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
                ingest_overrides={"input_uri": 1337},
            )

    def test_regex_replace_mappings(self):
        for mapping_fname in [
            "regex_replace_string.yaml",
            "regex_replace_list_to_string.yaml",
            "regex_replace_list_to_list.yaml",
            # both invalid mapping wont trigger InvalidMappingException, since their config is validated inside resolver logic
            "regex_replace_list_to_list_invalid.yaml",
            "regex_replace_list_to_list_invalid_2.yaml",
        ]:
            with self.subTest("Test mapping", file=mapping_fname):
                SourceMapping(
                    Path(
                        f"thebeast/tests/sample/mappings/regex_replace/{mapping_fname}"
                    )
                )

    def test_invalid_mapping_properties(self):
        for mapping_fname in [
            "invalid.yaml",
            "invalid_properties_1.yaml",
            "invalid_properties_2.yaml",
            "invalid_properties_3.yaml",
            "invalid_properties_4.yaml",
            "invalid_properties_5.yaml",
            "invalid_properties_6.yaml",
            "invalid_properties_info_1.yaml",
            "invalid_properties_info_2.yaml",
        ]:
            with self.subTest("Test mapping", file=mapping_fname):
                with self.assertRaises(InvalidMappingException):
                    SourceMapping(
                        Path(f"thebeast/tests/sample/mappings/{mapping_fname}")
                    )

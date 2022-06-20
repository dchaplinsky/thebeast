import unittest
from thebeast.ingest import CSVDictReader, CSVDictGlobReader, JSONLinesGlobReader, JSONGlobReader


class CSVDictReaderTests(unittest.TestCase):
    def test_csv_reader(self):
        ingestor = CSVDictReader(input_uri="thebeast/tests/sample/csv/gb_mps.csv")

        items = list(ingestor)
        self.assertEqual(len(items), 675)
        self.assertEqual(
            set(items[0].keys()),
            {
                "id",
                "name",
                "sort_name",
                "email",
                "twitter",
                "facebook",
                "group",
                "group_id",
                "area_id",
                "area",
                "chamber",
                "term",
                "start_date",
                "end_date",
                "image",
                "gender",
                "wikidata",
                "wikidata_group",
                "wikidata_area",
            },
        )

    def test_glob_csv_reader(self):
        ingestor = CSVDictGlobReader(input_uri="thebeast/tests/sample/csv/rada*.tsv")

        items = list(ingestor)
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


class JSONReadersTests(unittest.TestCase):
    def test_glob_jsonlines_reader(self):
        ingestor = JSONLinesGlobReader(input_uri="thebeast/tests/sample/json/*.jsonl")

        items = list(ingestor)

        self.assertEqual(len(items), 67)
        self.assertEqual(
            set(items[0].keys()),
            {
                "birth_date",
                "birth_place",
                "birth_placeLabel",
                "population",
                "mayorLabel",
                "itemLabel",
                "item",
                "age",
                "appointed",
                "mayor",
            },
        )

    def test_glob_json_reader(self):
        ingestor = JSONGlobReader(input_uri="thebeast/tests/sample/json/bank_ceos.json")

        items = list(ingestor)

        self.assertEqual(len(items), 81)
        self.assertEqual(
            set(items[0].keys()),
            {
                "appointed",
                "countryLabel",
                "item",
                "itemLabel",
                "person",
                "personLabel",
            },
        )

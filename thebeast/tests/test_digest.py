import unittest
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

from followthemoney.schema import Schema  # type: ignore
from thebeast.types import Record
from thebeast.conf.mapping import SourceMapping
from thebeast.contrib.ftm_ext import meta_factory


class MappingDigestTests(unittest.TestCase):
    def setUp(self):
        # Reseting the singletone.
        meta_factory.meta_cls = None

    def get_entities_by_schema(self, entities: List[Schema]) -> Dict[str, List[Schema]]:
        entities_by_schema = defaultdict(list)

        for entity in entities:
            entities_by_schema[entity["schema"]].append(entity)

        return entities_by_schema

    def test_valid_digest(self):
        for path in [
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
            Path("thebeast/tests/sample/mappings/ukrainian_mps_multiprocess.yaml"),
        ]:
            mapping = SourceMapping(path)

            items = [
                Record(
                    payload={
                        "name": "Ющенко Віктор Андрійович",
                        "party": "Блок Віктора Ющенка «Наша Україна»",
                        "district": "Багатомандатний округ",
                        "date_from": "14.05.2002",
                        "date_to": "23.01.2005[п. 1]",
                        "link": "https://uk.wikipedia.org/wiki/%D0%AE%D1%89%D0%B5%D0%BD%D0%BA%D0%BE_"
                        "%D0%92%D1%96%D0%BA%D1%82%D0%BE%D1%80_%D0%90%D0%BD%D0%B4%D1%80%D1%96%D0%B9%D0"
                        "%BE%D0%B2%D0%B8%D1%87",
                    },
                    record_no=1337,
                    input_uri="/dev/random",
                )
            ]

            entities = list(mapping.digestor.extract(items))
            self.assertEqual(len(entities), 4)

            entities_by_schema = self.get_entities_by_schema(entities)

            self.assertEqual(len(entities_by_schema["Person"]), 1)
            self.assertEqual(len(entities_by_schema["PublicBody"]), 1)
            self.assertEqual(len(entities_by_schema["Address"]), 1)
            self.assertEqual(len(entities_by_schema["Membership"]), 1)

            entity = entities_by_schema["Person"][0]
            self.assertIsNotNone(entity["id"])
            self.assertIn("Ющенко Віктор Андрійович", entity["properties"]["name"])
            self.assertIn("Віктор", entity["properties"]["firstName"])
            self.assertIn("Ющенко", entity["properties"]["lastName"])
            self.assertIn("Блок Віктора Ющенка «Наша Україна»", entity["properties"]["political"])
            self.assertIn("Андрійович", entity["properties"]["fatherName"])
            self.assertIn("wikipedia", entity["properties"]["sourceUrl"][0])
            self.assertIn("wikipedia", entity["properties"]["wikipediaUrl"][0])
            self.assertIn("Віктор Андрійович Ющенко", entity["properties"]["alias"])
            self.assertIn("Виктор Ющенко", entity["properties"]["alias"])
            self.assertIn("Віктор Ющенко", entity["properties"]["alias"])

            transformed_aliases = [
                prop for prop in entity["properties"]["alias"] if prop._meta.transformation is not None
            ]
            self.assertTrue(len(transformed_aliases) > 0)

            for prop in transformed_aliases:
                self.assertIn(
                    prop._meta.transformation,
                    [
                        "thebeast.contrib.transformers.names_transliteration()",
                        "thebeast.contrib.transformers.mixed_charset_fixer()",
                    ],
                )

            self.assertIn("Був депутатов 985 днів", entity["properties"]["notes"])
            self.assertIn(
                "Початок каденції: 2002-05-14, Блок Віктора Ющенка «Наша Україна»",
                entity["properties"]["notes"][0]._meta.test_field,
            )
            self.assertEqual(set(["Віктор", "Андрійович", "Ющенко"]), set(entity["properties"]["keywords"]))

            entity = entities_by_schema["PublicBody"][0]
            self.assertIsNotNone(entity["id"])
            self.assertIn("Верховна Рада України", entity["properties"]["name"])
            self.assertIn("ВРУ", entity["properties"]["name"])
            self.assertIn("wikipedia", entity["properties"]["wikipediaUrl"][0])
            self.assertIn(entities_by_schema["Address"][0]["id"], entity["properties"]["addressEntity"])

            entity = entities_by_schema["Address"][0]
            self.assertIsNotNone(entity["id"])
            self.assertIn("01008", entity["properties"]["postalCode"])
            self.assertIn("вул. М. Грушевського, 5", entity["properties"]["street"])

            entity = entities_by_schema["Membership"][0]
            self.assertIsNotNone(entity["id"])
            self.assertIn("2002-05-14", entity["properties"]["startDate"])
            self.assertIn("2005-01-23", entity["properties"]["endDate"])
            self.assertIn(entities_by_schema["PublicBody"][0]["id"], entity["properties"]["organization"])
            self.assertIn(entities_by_schema["Person"][0]["id"], entity["properties"]["member"])

            self.assertEqual(
                entity["properties"]["startDate"][0]._meta.transformation,
                "thebeast.contrib.transformers.anydate_parser(dayfirst=True)",
            )
            self.assertEqual(
                entity["properties"]["endDate"][0]._meta.transformation,
                "thebeast.contrib.transformers.anydate_parser(dayfirst=True)",
            )

            for entity in entities:
                for props in entity["properties"].values():
                    for prop in props:
                        self.assertEqual(prop._meta.locale, "uk")
                        if entity in entities_by_schema["Person"] or entity in entities_by_schema["Membership"]:
                            self.assertEqual(prop._meta.date, "2005-01-23")
                            self.assertEqual(
                                "/dev/random",
                                prop._meta.input_uri,
                            )
                            self.assertEqual(
                                1337,
                                prop._meta.record_no,
                            )

                        else:
                            self.assertEqual(prop._meta.date, None)
                            self.assertEqual(prop._meta.input_uri, "__mapping__")
                            self.assertEqual(prop._meta.record_no, 0)

    def test_surrogate_key(self):
        for path in [
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
            Path("thebeast/tests/sample/mappings/ukrainian_mps_multiprocess.yaml"),
        ]:
            mapping = SourceMapping(path)

            # There are two different records about the same person so we test now
            # if their surrogate keys are the same
            items = [
                Record(
                    {
                        "name": "Джемілєв Мустафа",
                        "party": "Блок Віктора Ющенка «Наша Україна»",
                        "district": "Багатомандатний округ",
                        "date_from": "14.05.2002",
                        "date_to": "25.05.2006",
                        "link": "https://uk.wikipedia.org/wiki/%D0%94%D0%B6%D0%B5%D0%BC%D1%96%D0%BB%D1%94"
                        "%D0%B2_%D0%9C%D1%83%D1%81%D1%82%D0%B0%D1%84%D0%B0",
                    }
                ),
                Record(
                    {
                        "name": "Джемілєв Мустафа",
                        "party": "Блок «Наша Україна»",
                        "district": "",
                        "date_from": "25.05.2006",
                        "date_to": "15.06.2007",
                        "link": "https://uk.wikipedia.org/wiki/%D0%94%D0%B6%D0%B5%D0%BC%D1%96%D0%BB%D1%94"
                        "%D0%B2_%D0%9C%D1%83%D1%81%D1%82%D0%B0%D1%84%D0%B0",
                    }
                ),
            ]

            entities = list(mapping.digestor.extract(items))
            self.assertEqual(len(entities), 6)

            entities_by_schema = self.get_entities_by_schema(entities)

            self.assertEqual(len(entities_by_schema["Person"]), 2)
            self.assertEqual(len(entities_by_schema["Membership"]), 2)

            self.assertEqual(entities_by_schema["Person"][0]["id"], entities_by_schema["Person"][1]["id"])

            self.assertIn(
                entities_by_schema["Person"][0]["id"], entities_by_schema["Membership"][0]["properties"]["member"]
            )
            self.assertIn(
                entities_by_schema["Person"][0]["id"], entities_by_schema["Membership"][1]["properties"]["member"]
            )
            self.assertIn(
                entities_by_schema["PublicBody"][0]["id"],
                entities_by_schema["Membership"][0]["properties"]["organization"],
            )
            self.assertIn(
                entities_by_schema["PublicBody"][0]["id"],
                entities_by_schema["Membership"][1]["properties"]["organization"],
            )

    def test_transformation_and_augmentation(self):
        for path in [
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"),
            Path("thebeast/tests/sample/mappings/ukrainian_mps_multiprocess.yaml"),
        ]:
            mapping = SourceMapping(path)

            # There are two different records about the same person so we test now
            # if their surrogate keys are the same
            items = [
                Record(
                    {
                        "name": "Джeмiлєв Мyстaфa",  # Mixed character set
                        "party": "Блок Віктора Ющенка «Наша Україна»",
                        "district": "Багатомандатний округ",
                        "date_from": "14.05.2002",
                        "date_to": "25.05.2006",
                        "link": "https://uk.wikipedia.org/wiki/%D0%94%D0%B6%D0%B5%D0%BC%D1%96%D0%BB%D1%94"
                        "%D0%B2_%D0%9C%D1%83%D1%81%D1%82%D0%B0%D1%84%D0%B0",
                    }
                )
            ]

            entities = list(mapping.digestor.extract(items))
            self.assertEqual(len(entities), 4)

            entities_by_schema = self.get_entities_by_schema(entities)

            entity = entities_by_schema["Person"][0]
            self.assertIn("Джемілєв Мустафа", entity["properties"]["name"])
            self.assertIn("Джемілєв", entity["properties"]["lastName"])
            self.assertIn("Мустафа", entity["properties"]["firstName"])
            self.assertNotIn("Джeмiлєв Мyстaфa", entity["properties"]["name"])
            self.assertIn("Mustafa Dzhemiliev", entity["properties"]["alias"])
            self.assertIn("Dzhemiliev Mustafa", entity["properties"]["alias"])

    def test_nested_digest(self):
        for path in [
            Path("thebeast/tests/sample/mappings/ukrainian_edr.yaml"),
            Path("thebeast/tests/sample/mappings/ukrainian_edr_multiprocess.yaml"),
        ]:
            mapping = SourceMapping(path)

            with open("thebeast/tests/sample/json/edr_sample.json", "r") as fp_in:
                items = [
                    Record(payload=rec, input_uri="edr_sample.json", record_no=i)
                    for i, rec in enumerate(json.load(fp_in))
                ]

            entities = list(mapping.digestor.extract(items))
            self.assertEqual(len(entities), 11)

            entities_by_schema = self.get_entities_by_schema(entities)

            self.assertEqual(len(entities_by_schema["Company"]), 2)
            self.assertEqual(len(entities_by_schema["Person"]), 3)
            self.assertEqual(len(entities_by_schema["Address"]), 3)
            self.assertEqual(len(entities_by_schema["Ownership"]), 3)

            for entity in entities:
                for props in entity["properties"].values():
                    for prop in props:
                        self.assertEqual(prop._meta.locale, "uk")
                        self.assertEqual(
                            "edr_sample.json",
                            prop._meta.input_uri,
                        )
                        self.assertIn(
                            prop._meta.record_no,
                            [0, 1],
                        )

    def test_no_meta(self):
        for path in [
            Path("thebeast/tests/sample/mappings/ru_mayors.yaml"),
            Path("thebeast/tests/sample/mappings/ru_mayors_multiprocess.yaml"),
        ]:
            mapping = SourceMapping(path)

            with open("thebeast/tests/sample/json/ru_mayors.jsonl", "r") as fp_in:
                items = [
                    Record(payload=json.loads(rec), input_uri="ru_mayors.jsonl", record_no=i)
                    for i, rec in enumerate(fp_in)
                ]

            entities = list(mapping.digestor.extract(items))
            self.assertEqual(len(entities), 67)

            entities_by_schema = self.get_entities_by_schema(entities)

            self.assertEqual(len(entities_by_schema["Person"]), 67)

            for entity in entities:
                for props in entity["properties"].values():
                    for prop in props:
                        # We deliberately disabled all the meta fields in this mapping
                        # so we are checking that those aren't populated in the results
                        for meta_field in meta_factory.DEFAULT_META_FIELDS:
                            self.assertNotIn(meta_field, prop._meta._fields)

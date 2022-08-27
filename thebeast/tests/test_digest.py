import unittest
from pathlib import Path
from collections import defaultdict

from thebeast.conf.mapping import SourceMapping


class MappingDigestTests(unittest.TestCase):
    def test_valid_digest(self):
        mapping = SourceMapping(Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"))

        items = [
            {
                "name": "Ющенко Віктор Андрійович",
                "party": "Блок Віктора Ющенка «Наша Україна»",
                "district": "Багатомандатний округ",
                "date_from": "14.05.2002",
                "date_to": "23.01.2005",
                "link": "https://uk.wikipedia.org/wiki/%D0%AE%D1%89%D0%B5%D0%BD%D0%BA%D0%BE_"
                "%D0%92%D1%96%D0%BA%D1%82%D0%BE%D1%80_%D0%90%D0%BD%D0%B4%D1%80%D1%96%D0%B9%D0"
                "%BE%D0%B2%D0%B8%D1%87",
            }
        ]

        entities = list(mapping.digestor.extract(items))
        self.assertEqual(len(entities), 4)

        entities_by_schema = defaultdict(list)

        for entity in entities:
            entities_by_schema[entity.schema.name].append(entity)

        self.assertEqual(len(entities_by_schema["Person"]), 1)
        self.assertEqual(len(entities_by_schema["PublicBody"]), 1)
        self.assertEqual(len(entities_by_schema["Address"]), 1)
        self.assertEqual(len(entities_by_schema["Membership"]), 1)

        entity = entities_by_schema["Person"][0]
        self.assertIsNotNone(entity.id)
        self.assertIn("Ющенко Віктор Андрійович", entity.properties["name"])
        self.assertIn("Віктор", entity.properties["firstName"])
        self.assertIn("Ющенко", entity.properties["lastName"])
        self.assertIn("Блок Віктора Ющенка «Наша Україна»", entity.properties["political"])
        self.assertIn("Андрійович", entity.properties["fatherName"])
        self.assertIn("wikipedia", entity.properties["sourceUrl"][0])
        self.assertIn("wikipedia", entity.properties["wikipediaUrl"][0])
        self.assertIn("Віктор Андрійович Ющенко", entity.properties["alias"])
        self.assertIn("Віктор Ющенко", entity.properties["alias"])
        self.assertEqual(set(["Віктор", "Андрійович", "Ющенко"]), set(entity.properties["keywords"]))

        entity = entities_by_schema["PublicBody"][0]
        self.assertIsNotNone(entity.id)
        self.assertIn("Верховна Рада України", entity.properties["name"])
        self.assertIn("ВРУ", entity.properties["name"])
        self.assertIn("wikipedia", entity.properties["wikipediaUrl"][0])
        self.assertIn(entities_by_schema["Address"][0].id, entity.properties["addressEntity"])

        entity = entities_by_schema["Address"][0]
        self.assertIsNotNone(entity.id)
        self.assertIn("01008", entity.properties["postalCode"])
        self.assertIn("вул. М. Грушевського, 5", entity.properties["street"])

        entity = entities_by_schema["Membership"][0]
        self.assertIsNotNone(entity.id)
        self.assertIn(entities_by_schema["PublicBody"][0].id, entity.properties["organization"])
        self.assertIn(entities_by_schema["Person"][0].id, entity.properties["member"])

    def test_surrogate_key(self):
        mapping = SourceMapping(Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"))

        # There are two different records about the same person so we test now
        # if their surrogate keys are the same
        items = [
            {
                "name": "Джемілєв Мустафа",
                "party": "Блок Віктора Ющенка «Наша Україна»",
                "district": "Багатомандатний округ",
                "date_from": "14.05.2002",
                "date_to": "25.05.2006",
                "link": "https://uk.wikipedia.org/wiki/%D0%94%D0%B6%D0%B5%D0%BC%D1%96%D0%BB%D1%94"
                "%D0%B2_%D0%9C%D1%83%D1%81%D1%82%D0%B0%D1%84%D0%B0",
            },
            {
                "name": "Джемілєв Мустафа",
                "party": "Блок «Наша Україна»",
                "district": "",
                "date_from": "25.05.2006",
                "date_to": "15.06.2007",
                "link": "https://uk.wikipedia.org/wiki/%D0%94%D0%B6%D0%B5%D0%BC%D1%96%D0%BB%D1%94"
                "%D0%B2_%D0%9C%D1%83%D1%81%D1%82%D0%B0%D1%84%D0%B0",
            },
        ]

        entities = list(mapping.digestor.extract(items))
        self.assertEqual(len(entities), 6)

        entities_by_schema = defaultdict(list)

        for entity in entities:
            entities_by_schema[entity.schema.name].append(entity)

        self.assertEqual(len(entities_by_schema["Person"]), 2)
        self.assertEqual(len(entities_by_schema["Membership"]), 2)

        self.assertEqual(entities_by_schema["Person"][0].id, entities_by_schema["Person"][1].id)

        self.assertIn(entities_by_schema["Person"][0].id, entities_by_schema["Membership"][0].properties["member"])
        self.assertIn(entities_by_schema["Person"][0].id, entities_by_schema["Membership"][1].properties["member"])
        self.assertIn(entities_by_schema["PublicBody"][0].id, entities_by_schema["Membership"][0].properties["organization"])
        self.assertIn(entities_by_schema["PublicBody"][0].id, entities_by_schema["Membership"][1].properties["organization"])

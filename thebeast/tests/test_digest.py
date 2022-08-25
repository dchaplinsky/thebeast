import unittest
from pathlib import Path
from thebeast.conf.mapping import SourceMapping


class MappingDigestTests(unittest.TestCase):
    def test_valid_digest(self):
        mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml")
        )

        items = [
            {
                "name": "Ющенко Віктор Андрійович",
                "party": "Блок Віктора Ющенка «Наша Україна»",
                "district": "Багатомандатний округ",
                "date_from": "14.05.2002",
                "date_to": "23.01.2005",
                "link": "https://uk.wikipedia.org/wiki/%D0%AE%D1%89%D0%B5%D0%BD%D0%BA%D0%BE_%D0%92%D1%96%D0%BA%D1%82%D0%BE%D1%80_%D0%90%D0%BD%D0%B4%D1%80%D1%96%D0%B9%D0%BE%D0%B2%D0%B8%D1%87",
            }
        ]

        entities = list(mapping.digestor.extract(items))
        self.assertEqual(len(entities), 3)
        for entity in entities:
            if entity.schema.name == "Person":
                self.assertIsNotNone(entity.id)
                self.assertIn("Ющенко Віктор Андрійович", entity.properties["name"])
                self.assertIn("Віктор", entity.properties["firstName"])
                self.assertIn("Ющенко", entity.properties["lastName"])
                self.assertIn("Андрійович", entity.properties["fatherName"])
                self.assertIn("wikipedia", entity.properties["sourceUrl"][0])
                self.assertIn("wikipedia", entity.properties["wikipediaUrl"][0])
                self.assertIn("Віктор Андрійович Ющенко", entity.properties["alias"][0])

            if entity.schema.name == "LegalBody":
                self.assertIsNotNone(entity.id)
                self.assertIn("Верховна Рада України", entity.properties["name"])
                self.assertIn("wikipedia", entity.properties["wikipediaUrl"][0])

            if entity.schema.name == "Address":
                self.assertIsNotNone(entity.id)
                self.assertIn("01008", entity.properties["postalCode"])
                self.assertIn("вул. М. Грушевського, 5", entity.properties["street"])

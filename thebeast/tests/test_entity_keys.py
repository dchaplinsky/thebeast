import unittest
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

from followthemoney.schema import Schema  # type: ignore
from thebeast.types import Record
from thebeast.conf.mapping import SourceMapping
from thebeast.contrib.ftm_ext import meta_factory

"""
  Tests for entity keys resolvers
"""


class EntityKeysTests(unittest.TestCase):
    def test_asterisk_key_generator(self):
        mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/keys_resolver/asterisk_keys.yaml")
        )

        items = [
            Record(payload={"name": "Ющенко Віктор Андрійович"}),
            Record(
                payload={"name": "Ющенко Віктор Андрійович", "birth_date": "1954-02-23"}
            ),
            Record(
                payload={
                    "name": "Ющенко Віктор Андрійович",
                    "birth_date": "1954-02-23",
                    "notes": "Третій Президент України",
                }
            ),
        ]

        entities = list(ent.payload for ent in mapping.digestor.extract(items))
        self.assertEqual(3, len(entities))

        # ids must differ with each row
        self.assertEqual("c1d4c4652b8b9a8d5cda22d508e497a12dd9d07f", entities[0]["id"])
        self.assertEqual("c131fc0732f46173b22c8698d0cc5d0d220a7932", entities[1]["id"])
        self.assertEqual("4de61b4fc100bf0a397898a5067be46a28e26a16", entities[2]["id"])

    def test_asterisk_key_resolver_returns_same_keys_as_manual(self):
        asterisk_mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/keys_resolver/asterisk_keys.yaml")
        )
        manual_mapping = SourceMapping(
            Path("thebeast/tests/sample/mappings/keys_resolver/manual_keys.yaml")
        )

        items = [
            Record(payload={"name": "Ющенко Віктор Андрійович"}),
            Record(
                payload={"name": "Ющенко Віктор Андрійович", "birth_date": "1954-02-23"}
            ),
            Record(
                payload={
                    "name": "Ющенко Віктор Андрійович",
                    "birth_date": "1954-02-23",
                    "notes": "Третій Президент України",
                }
            ),
        ]

        asterisk_entities = list(
            ent.payload for ent in asterisk_mapping.digestor.extract(items)
        )
        manual_entities = list(
            ent.payload for ent in manual_mapping.digestor.extract(items)
        )

        # keys will be same for 1st and 2nd rows because both have the same keys
        self.assertEqual(manual_entities[0]["id"], asterisk_entities[0]["id"])
        self.assertEqual(manual_entities[1]["id"], asterisk_entities[1]["id"])

        # manual_keys will ignore `notes`, so keys will differ
        self.assertNotEqual(manual_entities[2]["id"], asterisk_entities[2]["id"])

    def test_entity_keys_on_entity_field(self):
        for path in [
            Path("thebeast/tests/sample/mappings/keys_resolver/entity_keys.yaml"),
            Path(
                "thebeast/tests/sample/mappings/keys_resolver/entity_keys_wildcard.yaml"
            ),
        ]:
            mapping = SourceMapping(path)

            items = [
                Record(payload={"name": "Ivan Sraka", "company": "Sraka, LTD."}),
                Record(payload={"name": "Ivan Sraka"}),
            ]

            entities = [*mapping.digestor.extract(items)]
            self.assertEqual(6, len(entities))

            self.assertEqual("Person", entities[0].payload["schema"])
            self.assertEqual("Company", entities[1].payload["schema"])
            self.assertEqual("Employment", entities[2].payload["schema"])

            self.assertTrue(entities[0].valid)
            self.assertTrue(entities[1].valid)
            self.assertTrue(entities[2].valid)

            self.assertEqual(
                "17dec550a297076989f408f075db145c3f72b80a", entities[0].payload["id"]
            )
            self.assertEqual(
                "178e4423135e4b92d81049984b41ff524c1f5641", entities[1].payload["id"]
            )
            self.assertEqual(
                "60781e1346aa5d396d3d6ed19743f8ae91dc9058", entities[2].payload["id"]
            )

            self.assertEqual("Person", entities[3].payload["schema"])
            self.assertEqual("Company", entities[4].payload["schema"])
            self.assertEqual("Employment", entities[5].payload["schema"])

            self.assertTrue(entities[3].valid)
            self.assertFalse(entities[4].valid)
            self.assertFalse(entities[5].valid)

            # person keys are the same
            self.assertEqual(entities[0].payload["id"], entities[3].payload["id"])
            # second `company` is not generated
            self.assertEqual(None, entities[4].payload["id"])
            # `employment` id will differ because second company entity is not degenerated
            self.assertNotEqual(entities[2].payload["id"], entities[5].payload["id"])

    def test_entity_keys_on_entity_field_with_wrong_mapping_entity_order(self):
        mapping = SourceMapping(
            Path(
                "thebeast/tests/sample/mappings/keys_resolver/entity_keys_wildcard_shuffled.yaml"
            )
        )

        items = [
            Record(payload={"name": "Ivan Sraka", "company": "Sraka, LTD."}),
            Record(payload={"name": "Ivan Sraka"}),
        ]

        entities = [*mapping.digestor.extract(items)]
        self.assertEqual(6, len(entities))

        self.assertEqual("Employment", entities[0].payload["schema"])
        self.assertEqual("Company", entities[1].payload["schema"])
        self.assertEqual("Person", entities[2].payload["schema"])

        # both employment ids will be `None` since it can't resolve it's related entities, being before them in mapping
        self.assertEqual(None, entities[0].payload["id"])
        self.assertEqual(None, entities[3].payload["id"])

        # also ensure these entities are invalid
        self.assertFalse(entities[0].valid)
        self.assertFalse(entities[3].valid)

        self.assertEqual(
            "17dec550a297076989f408f075db145c3f72b80a", entities[2].payload["id"]
        )

        # Second `Company` is also None since it's empty
        self.assertEqual(None, entities[4].payload["id"])
        self.assertFalse(entities[4].valid)
        self.assertEqual(entities[2].payload["id"], entities[5].payload["id"])

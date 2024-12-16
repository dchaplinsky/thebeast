import unittest
import sys
import json
from io import StringIO
from followthemoney import model as ftm  # type: ignore

from thebeast.dump import StatementsCSVWriter
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from thebeast.digest.utils import deflate_entity, make_entity
from thebeast.tests.test_dump_entity import CaptureStdout
from thebeast.dump.statements import stmt_key

"""
  Tests for entities dump / StatementsCSVWriter
"""


class MappingDumpTests(unittest.TestCase):
    def test_empty_dump(self):
        with CaptureStdout():
            dumper = StatementsCSVWriter(output_uri="-", meta_fields=[])
            dumper.write_entities([], flush=True)

            # should write csv header
            sys.stdout.seek(0)
            self.assertEqual(
                sys.stdout.read(), "id,entity_id,prop,prop_type,schema,value\r\n"
            )

    def test_empty_dump_with_meta(self):
        with CaptureStdout():
            dumper = StatementsCSVWriter(output_uri="-", meta_fields=["foo", "bar"])
            dumper.write_entities([], flush=True)

            # should write csv header with additional meta columns
            sys.stdout.seek(0)
            self.assertEqual(
                sys.stdout.read(),
                "id,entity_id,prop,prop_type,schema,value,meta:foo,meta:bar\r\n",
            )

    def test_empty_entity_dump(self):
        with CaptureStdout():
            dumper = StatementsCSVWriter(output_uri="-", meta_fields=[])
            entity = ftm.make_entity("Person")
            dumper.write_entities([deflate_entity(entity)])

            # should write only csv header for empty entity
            sys.stdout.seek(0)
            self.assertEqual(
                sys.stdout.read(), "id,entity_id,prop,prop_type,schema,value\r\n"
            )

        with CaptureStdout():
            dumper = StatementsCSVWriter(output_uri="-", error_uri="-", meta_fields=[])
            entity = make_entity("Person")
            dumper.write_entities([deflate_entity(entity)])

            # should write only entity_id statement with empty entity_id
            sys.stdout.seek(0)
            self.assertEqual(
                sys.stdout.readline(), "id,entity_id,prop,prop_type,schema,value\r\n"
            )
            self.assertEqual(
                sys.stdout.readline(),
                "44a60d21bd20bfebd2ba1190aff78ed7600a4d19,,id,id,Person,\r\n",
            )
            self.assertEqual(sys.stdout.readline(), "")

        with CaptureStdout():
            dumper = StatementsCSVWriter(
                output_uri="/dev/stdout", error_uri="/dev/stderr", meta_fields=[]
            )
            entity = make_entity("Person")
            dumper.write_entities([deflate_entity(entity)])

            # for entity with empty entity_id stdout (output_uri) will only have csv header
            sys.stdout.seek(0)
            self.assertEqual(
                sys.stdout.read(), "id,entity_id,prop,prop_type,schema,value\r\n"
            )

            # and stderr (error_uri) will have empty id statement
            sys.stderr.seek(0)
            self.assertEqual(
                sys.stderr.readline(), "id,entity_id,prop,prop_type,schema,value\r\n"
            )
            self.assertEqual(
                sys.stderr.readline(),
                "44a60d21bd20bfebd2ba1190aff78ed7600a4d19,,id,id,Person,\r\n",
            )
            self.assertEqual(sys.stderr.readline(), "")

    def test_full_entity_dump(self):
        with CaptureStdout():
            dumper = StatementsCSVWriter(
                output_uri="-",
                error_uri="/dev/stderr",
                meta_fields=[
                    "record_no",
                    "input_uri",
                    "locale",
                    "date",
                    "transformation",
                    "test_field",
                ],
            )

            entity = make_entity("Person")
            entity.set("name", "Ющенко Віктор Андрійович")
            entity.set("firstName", "Віктор")
            entity.set("lastName", "Ющенко")
            entity.set("fatherName", "Андрійович")
            entity.set(
                "sourceUrl", "https://uk.wikipedia.org/wiki/Ющенко_Віктор_Андрійович"
            )
            entity.make_id(["foo", "bar"])

            empty_entity = make_entity("Person")

            dumper.write_entities(
                [deflate_entity(entity), deflate_entity(empty_entity)]
            )

            # stdout will have statements all for entity
            sys.stdout.seek(0)

            with open(
                "thebeast/tests/sample/csv/statements/person_statements.csv"
            ) as file:
                for line in file:
                    expected = line.rstrip()
                    actual = sys.stdout.readline().rstrip()

                    self.assertEqual(
                        expected, actual, "Not expected dump statement in stdout"
                    )

            self.assertEqual(
                "", sys.stdout.readline(), "There is something left in stdout"
            )

            # statement dumper will still give the statement for empty entity id
            sys.stderr.seek(0)

            with open(
                "thebeast/tests/sample/csv/statements/empty_person_statements.csv"
            ) as file:
                for line in file:
                    expected = line.rstrip()
                    actual = sys.stderr.readline().rstrip()
                    self.assertEqual(
                        expected, actual, "Not expected dump statement in stderr"
                    )

            self.assertEqual(
                "", sys.stderr.readline(), "There is something left in stderr"
            )

        with CaptureStdout():
            dumper = StatementsCSVWriter(
                output_uri="-",
                error_uri="-",
                meta_fields=[
                    "record_no",
                    "input_uri",
                    "locale",
                    "date",
                    "transformation",
                    "test_field",
                ],
            )

            dumper.write_entities(
                [deflate_entity(entity), deflate_entity(empty_entity)]
            )
            sys.stdout.seek(0)

            with open(
                "thebeast/tests/sample/csv/statements/person_statements.csv"
            ) as file:
                for line in file:
                    expected = line.rstrip()
                    actual = sys.stdout.readline().rstrip()
                    self.assertEqual(
                        expected, actual, "Not expected dump statement in stdout"
                    )

            with open(
                "thebeast/tests/sample/csv/statements/empty_person_statements.csv"
            ) as file:
                # skip csv header from saved file
                # we do not need to check it since we're checking same output stream as before
                next(file)
                for line in file:
                    expected = line.rstrip()
                    actual = sys.stdout.readline().rstrip()
                    self.assertEqual(
                        expected, actual, "Not expected dump statement in stdout"
                    )

            self.assertEqual(
                "", sys.stdout.readline(), "There is something left in stdout"
            )

    def test_entity_with_meta_dump(self):
        with CaptureStdout():
            dumper = StatementsCSVWriter(
                output_uri="-",
                error_uri="-",
                meta_fields=[
                    "record_no",
                    "input_uri",
                    "locale",
                    "date",
                    "transformation",
                    "test_field",
                ],
            )

            entity = make_entity("Person")
            entity.set("name", StrProxy("Срака Іван", meta={"locale": "uk"}))
            entity.set("firstName", StrProxy("Іван", meta={"locale": "en"}))
            entity.set(
                "lastName",
                StrProxy("Срака", meta={"locale": "uk", "date": "01.05.1999"}),
            )
            entity.make_id(["foo", "bar"])

            dumper.write_entities([deflate_entity(entity)])
            sys.stdout.seek(0)

            with open(
                "thebeast/tests/sample/csv/statements/meta_person_statements.csv"
            ) as file:
                # skip csv header from saved file
                # we do not need to check it since we're checking same output stream as before
                for line in file:
                    expected = line.rstrip()
                    actual = sys.stdout.readline().rstrip()
                    self.assertEqual(
                        expected, actual, "Not expected dump statement in stdout"
                    )

            self.assertEqual(
                "", sys.stdout.readline(), "There is something left in stdout"
            )

    def test_statement_id(self):
        with CaptureStdout():
            # test entity id generated
            key = stmt_key(entity_id="foo", prop="name", value="Іван Срака")
            self.assertEqual(key, "12747891a8c16675b628513a1c95a32cc501a703")

            # id will be different for StrProxy with same value
            prop = StrProxy("Іван Срака")
            key = stmt_key(entity_id="foo", prop="name", value=prop)
            self.assertEqual(key, "e2bba1355573a34e3058e0a0ec11888c3f3b8a5b")

            # assert default meta is used when generating key
            prop = StrProxy(
                "Іван Срака",
                meta={"locale": "ru", "date": "2020-01-01", "transformation": ""},
            )
            prop2 = StrProxy(
                "Іван Срака",
                meta={"locale": "ru", "date": "2020-01-01", "transformation": ""},
            )

            key1 = stmt_key(
                entity_id="foo",
                prop="name",
                value=prop,
                meta_for_stmt_id=["locale", "date", "transformation"],
            )
            key2 = stmt_key(entity_id="foo", prop="name", value=prop)
            self.assertEqual(key1, key2)

            # ensure additional meta values are filtered
            # we asking only for locale - which is same - so we will get same statement_id
            prop = StrProxy("Іван Срака", meta={"locale": "ua", "date": "2020-01-01"})
            prop2 = StrProxy("Іван Срака", meta={"locale": "ua", "date": "1999-01-01"})

            key1 = stmt_key(
                entity_id="foo", prop="name", value=prop, meta_for_stmt_id=["locale"]
            )
            key2 = stmt_key(
                entity_id="foo", prop="name", value=prop2, meta_for_stmt_id=["locale"]
            )
            self.assertEqual(key1, key2)

            # and for date field ids must be different
            key1 = stmt_key(
                entity_id="foo", prop="name", value=prop, meta_for_stmt_id=["date"]
            )
            key2 = stmt_key(
                entity_id="foo", prop="name", value=prop2, meta_for_stmt_id=["date"]
            )
            self.assertNotEqual(key1, key2)

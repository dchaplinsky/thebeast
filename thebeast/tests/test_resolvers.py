import unittest
import re

from thebeast.digest.resolvers import (
    _resolve_literal,
    _resolve_entity,
    _resolve_column,
    _resolve_regex_split,
    _resolve_regex_first,
    _resolve_transformer,
    _resolve_augmentor,
    ResolveContext,
)
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy


class ResolversTests(unittest.TestCase):
    def test_resolve_literal(self):
        ctx = ResolveContext(record={}, property_values=[], entity=None, statements_meta={}, variables={})

        self.assertEqual(_resolve_literal("foobar", ctx), ["foobar"])
        self.assertEqual(_resolve_literal(StrProxy("foobar"), ctx), ["foobar"])
        self.assertIsInstance(_resolve_literal("foobar", ctx)[0], StrProxy)

        ctx.statements_meta = {"locale": "de"}
        self.assertEqual(_resolve_literal("foobar", ctx)[0]._meta.locale, "de")
        self.assertEqual(_resolve_literal(StrProxy("foobar"), ctx)[0]._meta.locale, "de")

        ctx.property_values = [StrProxy("Hell yeah")]

        self.assertSetEqual(set(_resolve_literal("foobar", ctx)), set(["foobar", "Hell yeah"]))

    def test_resolve_entity(self):
        ctx = ResolveContext(record={}, property_values=[], entity=None, statements_meta={}, variables={})

        self.assertTrue(re.match(r"^[0-9a-zA-Z]([0-9a-zA-Z\.\-]*[0-9a-zA-Z])?$", _resolve_entity("foobar", ctx)[0]))
        self.assertTrue(
            re.match(r"^[0-9a-zA-Z]([0-9a-zA-Z\.\-]*[0-9a-zA-Z])?$", _resolve_entity(StrProxy("foobar"), ctx)[0])
        )

        ctx.statements_meta = {"locale": "de"}
        self.assertEqual(_resolve_entity("foobar", ctx)[0]._meta.locale, "de")
        self.assertEqual(_resolve_entity(StrProxy("foobar"), ctx)[0]._meta.locale, "de")

        ctx.property_values = [StrProxy("Hell yeah")]
        self.assertEqual(len(_resolve_entity("foobar", ctx)), 2)

    def test_resolve_column(self):
        ctx = ResolveContext(
            record={"foo": "bar", "baz": {"foobar": "baz"}, "q": 42},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        self.assertEqual(_resolve_column("foobar", ctx), [])
        self.assertEqual(_resolve_column("foo", ctx), ["bar"])
        self.assertIsInstance(_resolve_column("foo", ctx)[0], StrProxy)

        self.assertEqual(_resolve_column("baz.foobar", ctx), ["baz"])
        self.assertIsInstance(_resolve_column("baz.foobar", ctx)[0], StrProxy)

        self.assertEqual(_resolve_column("q", ctx), ["42"])
        self.assertIsInstance(_resolve_column("q", ctx)[0], StrProxy)

        ctx.statements_meta = {"locale": "de"}
        self.assertEqual(_resolve_column("foo", ctx)[0]._meta.locale, "de")

        ctx.property_values = [StrProxy("Hell yeah")]
        self.assertSetEqual(set(_resolve_column("foo", ctx)), set(["bar", "Hell yeah"]))

    def test_resolve_regex_split(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy("1,2,3"), StrProxy("4,5,6")],
            entity=None,
            statements_meta={},
            variables={},
        )

        self.assertSetEqual(set(_resolve_regex_split(",", ctx)), set(["1", "2", "3", "4", "5", "6"]))

        ctx.statements_meta = {"locale": "de"}
        for val in _resolve_regex_split(",", ctx):
            self.assertIsInstance(val, StrProxy)
            self.assertEqual(val._meta.locale, None)

        ctx.property_values = [StrProxy("1,2,3", meta={"locale": "php"}), StrProxy("4,5,6", meta={"locale": "py"})]

        for val in _resolve_regex_split(",", ctx):
            if val < "4":
                self.assertEqual(val._meta.locale, "php")
            else:
                self.assertEqual(val._meta.locale, "py")

    def test_resolve_regex_first(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy("1,2,3"), StrProxy("4,5,6")],
            entity=None,
            statements_meta={},
            variables={},
        )

        self.assertSetEqual(
            set(_resolve_regex_first(r"\d+", ctx)),
            set(
                [
                    "1",
                    "4",
                ]
            ),
        )

        ctx.statements_meta = {"locale": "de"}
        for val in _resolve_regex_first(r"\d+", ctx):
            self.assertIsInstance(val, StrProxy)
            self.assertEqual(val._meta.locale, None)

        ctx.property_values = [StrProxy("1,2,3", meta={"locale": "php"}), StrProxy("4,5,6", meta={"locale": "py"})]

        for val in _resolve_regex_first(r"\d+", ctx):
            if val < "4":
                self.assertEqual(val._meta.locale, "php")
            else:
                self.assertEqual(val._meta.locale, "py")

        self.assertSetEqual(
            set(_resolve_regex_first(r"(\d+)(,)", ctx)),
            set(
                [
                    "1",
                    "4",
                ]
            ),
        )

    def test_resolve_transformer(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy("05.06.07")],
            entity=None,
            statements_meta={},
            variables={},
        )

        val = _resolve_transformer("thebeast.contrib.transformers.anydate_parser", ctx)[0]
        self.assertIsInstance(val, StrProxy)
        self.assertEqual(val, "2007-05-06")

        val = _resolve_transformer({"name": "thebeast.contrib.transformers.anydate_parser"}, ctx)[0]
        self.assertEqual(val, "2007-05-06")

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"dayfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2007-06-05")

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"yearfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2005-06-07")

        ctx.property_values = [StrProxy("05.06.07", meta={"locale": "php"})]

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"yearfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2005-06-07")
        self.assertEqual(val._meta.locale, "php")

    def test_resolve_augmentor(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy("Ігор Гіркін")],
            entity=None,
            statements_meta={},
            variables={},
        )

        vals = _resolve_transformer("thebeast.contrib.transformers.names_transliteration", ctx)
        self.assertIn("Ігор Гіркін", vals)
        self.assertIn("Ihor Hirkin", vals)
        self.assertIn("Igor Girkin", vals)

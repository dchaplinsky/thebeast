import unittest
import re

from thebeast.digest.resolvers import (
    _resolve_literal,
    _resolve_entity,
    _resolve_column,
    _resolve_regex_split,
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

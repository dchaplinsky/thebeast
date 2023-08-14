import unittest
import re

from thebeast.digest.resolvers import (
    _resolve_literal,
    _resolve_entity,
    _resolve_column,
    _resolve_regex_split,
    _resolve_regex_first,
    _resolve_regex_replace,
    _resolve_augmentor,
    _resolve_template,
    _resolve_property,
    ResolveContext,
)
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from thebeast.digest.utils import make_entity


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

    def test_resolve_regex_replace(self):
        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        with self.subTest("Test string regex"):
            ctx.property_values = [StrProxy("foo 123 bar")]
            self.assertEqual(_resolve_regex_replace({"regex": "[^a-z]", "replace": ""}, ctx)[0], "foobar")

        with self.subTest("Test replace groups"):
            ctx.property_values = [StrProxy("foo 123 bar")]
            self.assertEqual(
                _resolve_regex_replace({"regex": "([a-z]{3})\\s([0-9]{3})\\s([a-z]{3})", "replace": "\\1\\3"}, ctx)[0],
                "foobar",
            )

        with self.subTest("Test replace for multiple inputs"):
            ctx.property_values = [StrProxy("foo 123 bar"), StrProxy("456 baz qux")]
            self.assertEqual(_resolve_regex_replace({"regex": "[^0-9]", "replace": ""}, ctx), ["123", "456"])

        with self.subTest("Test replace with multiple regex"):
            ctx.property_values = [StrProxy("foo 123 bar")]
            self.assertEqual(_resolve_regex_replace({"regex": ["foo", "bar"], "replace": ""}, ctx)[0], " 123 ")

        with self.subTest("Test replace with multiple regex and multiple replaces"):
            ctx.property_values = [StrProxy("foo 123 bar")]
            self.assertEqual(
                _resolve_regex_replace({"regex": ["foo", "bar"], "replace": ["baz", "qux"]}, ctx), ["baz 123 qux"]
            )

        with self.subTest("Test replace with multiple regex and multiple replaces and multiple inputs"):
            ctx.property_values = [StrProxy("foo 123 bar"), StrProxy("bar 321 foo")]
            self.assertEqual(
                _resolve_regex_replace({"regex": ["foo", "bar"], "replace": ["baz", "qux"]}, ctx),
                ["baz 123 qux", "qux 321 baz"],
            )

        with self.subTest("Test replace throws error if replace count differs from regex count"):
            ctx.property_values = [StrProxy("foo 123 bar")]

            self.assertRaises(
                ValueError,
                _resolve_regex_replace,
                {"regex": ["foo", "bar"], "replace": ["baz"]},
                ctx,
            )

    def test_resolve_augmentor(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy("Ігор Гіркін")],
            entity=None,
            statements_meta={},
            variables={},
        )

        vals = _resolve_augmentor("thebeast.contrib.transformers.names_transliteration", ctx)
        self.assertIn("Ігор Гіркін", vals)
        self.assertIn("Ihor Hirkin", vals)
        self.assertIn("Igor Girkin", vals)

        transformed_aliases = [prop for prop in vals if prop._meta.transformation is not None]
        self.assertTrue(len(transformed_aliases) > 0)

        for prop in transformed_aliases:
            self.assertEqual(
                prop._meta.transformation,
                "thebeast.contrib.transformers.names_transliteration()",
            )

    def test_resolve_property(self):
        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={"$foobar": [StrProxy("bar")]},
        )

        val = _resolve_property("$foobar", ctx)[0]
        self.assertEqual("bar", val)
        self.assertIsInstance(val, StrProxy)

        ctx.entity = make_entity("Person", "key_prefix")
        ctx.entity.add("name", ["baz"])

        val = _resolve_property("name", ctx)[0]
        self.assertEqual("baz", val)
        self.assertIsInstance(val, StrProxy)

    def test_resolve_template(self):
        entity = make_entity("Person", "key_prefix")
        entity.add("name", ["3"])

        ctx = ResolveContext(
            record={"foo": "1"},
            property_values=[StrProxy("2")],
            entity=entity,
            statements_meta={"locale": 4},
            variables={"$foo": [StrProxy("5")]},
        )

        val = _resolve_template(
            "{{ record.foo }} {{ property_value }} {{ entity.name[0] }} {{ meta.locale }} "
            "{{ variables['$foo']|join('') }}",
            ctx,
        )[0]
        self.assertEqual("1 2 3 4 5", val)
        self.assertIsInstance(val, StrProxy)

    # TODO: test for _resolve_meta

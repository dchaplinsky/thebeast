import unittest
import re

from thebeast.digest.resolvers import (
    _resolve_literal,
    _resolve_entity,
    _resolve_column,
    _resolve_regex_split,
    _resolve_regex_first,
    _resolve_regex_replace,
    _resolve_transformer,
    _resolve_augmentor,
    _resolve_template,
    _resolve_property,
    ResolveContext,
)
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from thebeast.digest.utils import make_entity


class ResolversTests(unittest.TestCase):
    def test_anydate_parser(self):
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
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.anydate_parser()")

        val = _resolve_transformer({"name": "thebeast.contrib.transformers.anydate_parser"}, ctx)[0]
        self.assertEqual(val, "2007-05-06")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.anydate_parser()")

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"dayfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2007-06-05")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.anydate_parser(dayfirst=True)")

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"yearfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2005-06-07")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.anydate_parser(yearfirst=True)")

        ctx.property_values = [StrProxy("05.06.07", meta={"locale": "php"})]

        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"yearfirst": True}}, ctx
        )[0]
        self.assertEqual(val, "2005-06-07")
        self.assertEqual(val._meta.locale, "php")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.anydate_parser(yearfirst=True)")

    def test_trim_string(self):
        ctx = ResolveContext(
            record={},
            property_values=[StrProxy(" foo bar ")],
            entity=None,
            statements_meta={},
            variables={},
        )

        val = _resolve_transformer({"name": "thebeast.contrib.transformers.trim_string", "params": {}}, ctx)[0]
        self.assertEqual(val, "foo bar")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.trim_string()")

        ctx.property_values = [StrProxy("foo bar,. ")]
        val = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.trim_string", "params": {"strip": " ,."}}, ctx
        )[0]
        self.assertEqual(val, "foo bar")
        self.assertEqual(val._meta.transformation, "thebeast.contrib.transformers.trim_string(strip= ,.)")

    def test_normalize_email(self):
        param_list = [
            (StrProxy("foobar@@@@"), "foobar@@@@"),
            (StrProxy("gmail.com"), "gmail.com"),
            # it also converts email to lowercase
            (StrProxy("FooBar@GMail.com"), "foobar@gmail.com"),
            (StrProxy("foo.dot@gmail.com"), "foodot@gmail.com"),
            (StrProxy("foo+plus@gmail.com"), "foo@gmail.com"),
            # we fix inly user name, dont touch the domain
            (StrProxy("foo+plus@g.mail.com"), "foo@g.mail.com"),
            # fixme: it contains spaces - so we assume it's not an email and return it as is
            (StrProxy(" foo.dot@gmail.com "), " foo.dot@gmail.com "),
        ]

        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        for input_val, expected_result in param_list:
            with self.subTest():
                ctx.property_values = [StrProxy(input_val)]

                actual_result = _resolve_transformer({"name": "thebeast.contrib.transformers.normalize_email"}, ctx)[0]
                self.assertEqual(actual_result, expected_result)

import unittest

from thebeast.digest.resolvers import (
    _resolve_transformer,
    ResolveContext,
)
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy


class ResolversTests(unittest.TestCase):
    def test_anydate_parser(self):
        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        with self.subTest("Test anydate_parser"):
            ctx.property_values = [StrProxy("05.06.07")]
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

        with self.subTest("Test anydate_parser throws exception on invalid value"):
            ctx.property_values = [StrProxy("05.06.07"), StrProxy("fooBAR")]
            self.assertRaises(
                ValueError,
                _resolve_transformer,
                {"name": "thebeast.contrib.transformers.anydate_parser"},
                ctx,
            )

        with self.subTest("Test error is not thrown with silent mode, and only invalid value is skipped"):
            ctx.property_values = [StrProxy("05.06.07"), StrProxy("fooBAR")]
            actual_result = _resolve_transformer(
                {"name": "thebeast.contrib.transformers.anydate_parser", "params": {"silent": True}}, ctx
            )
            self.assertEqual(actual_result, ["2007-05-06"])

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

    def test_decode_html_entities(self):
        param_list = [
            (StrProxy("foobar"), "foobar"),
            (StrProxy("<foobar>"), "<foobar>"),
            (StrProxy("&lt;foobar&#62;"), "<foobar>"),
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

                actual_result = _resolve_transformer(
                    {"name": "thebeast.contrib.transformers.decode_html_entities"}, ctx
                )[0]
                self.assertEqual(actual_result, expected_result)

    def test_pad_string(self):
        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        ctx.property_values = [StrProxy("1234")]
        actual_result = _resolve_transformer(
            {"name": "thebeast.contrib.transformers.pad_string", "params": {"length": "5", "pad_char": "0"}}, ctx
        )[0]
        self.assertEqual(actual_result, "12340")

        ctx.property_values = [StrProxy("1234")]
        actual_result = _resolve_transformer(
            {
                "name": "thebeast.contrib.transformers.pad_string",
                "params": {"length": "5", "pad_char": "5", "align": "right"},
            },
            ctx,
        )[0]
        self.assertEqual(actual_result, "51234")

        ctx.property_values = [StrProxy("1234")]
        self.assertRaises(
            ValueError,
            _resolve_transformer,
            {"name": "thebeast.contrib.transformers.pad_string", "params": {"length": "5", "align": "foobar"}},
            ctx,
        )

    def test_convert_case(self):
        param_list = [
            (StrProxy("FoObAr"), "upper", "FOOBAR"),
            (StrProxy("FoObAr"), "lower", "foobar"),
        ]

        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        for input_val, case, expected_result in param_list:
            with self.subTest("Test case convers", case=case):
                ctx.property_values = [StrProxy(input_val)]
                actual_result = _resolve_transformer(
                    {"name": "thebeast.contrib.transformers.convert_case", "params": {"case": case}}, ctx
                )[0]
                self.assertEqual(actual_result, expected_result)

        with self.subTest("Test error is thrown"):
            ctx.property_values = [StrProxy("fooBAR")]
            self.assertRaises(
                ValueError,
                _resolve_transformer,
                {"name": "thebeast.contrib.transformers.convert_case", "params": {"case": "foobar"}},
                ctx,
            )

    def test_from_unixtime(self):
        param_list = [("1643839200", "2022-02-02 22:00:00"), ("1643895202", "2022-02-03 13:33:22")]

        ctx = ResolveContext(
            record={},
            property_values=[],
            entity=None,
            statements_meta={},
            variables={},
        )

        for input_val, expected_result in param_list:
            with self.subTest("Test date from unixtime", expected_result=expected_result):
                ctx.property_values = [StrProxy(input_val)]
                actual_result = _resolve_transformer({"name": "thebeast.contrib.transformers.from_unixtime"}, ctx)[0]
                self.assertEqual(actual_result, expected_result)
                self.assertEqual(actual_result._meta.transformation, "thebeast.contrib.transformers.from_unixtime()")

        with self.subTest("Zero unixtime is ignored by default"):
            ctx.property_values = [StrProxy("0"), StrProxy("1691528400")]
            actual_result = _resolve_transformer({"name": "thebeast.contrib.transformers.from_unixtime"}, ctx)
            self.assertEqual(actual_result, ["2023-08-08 21:00:00"])

        with self.subTest("Zero unixtime is not ignored if param is set"):
            ctx.property_values = [StrProxy("0"), StrProxy("1691528400")]
            actual_result = _resolve_transformer(
                {"name": "thebeast.contrib.transformers.from_unixtime", "params": {"skip_zero_date": False}}, ctx
            )
            self.assertEqual(actual_result, ["1970-01-01 00:00:00", "2023-08-08 21:00:00"])

        with self.subTest("Test error is thrown without silent mode"):
            ctx.property_values = [StrProxy("1691528400"), StrProxy("fooBAR")]
            self.assertRaises(
                ValueError,
                _resolve_transformer,
                {"name": "thebeast.contrib.transformers.from_unixtime", "params": {"silent": False}},
                ctx,
            )

        with self.subTest("Test error is not thrown with silent mode, and only invalid value is skipped"):
            ctx.property_values = [StrProxy("1691528400"), StrProxy("fooBAR")]
            actual_result = _resolve_transformer(
                {"name": "thebeast.contrib.transformers.from_unixtime", "params": {"silent": True}}, ctx
            )
            self.assertEqual(actual_result, ["2023-08-08 21:00:00"])

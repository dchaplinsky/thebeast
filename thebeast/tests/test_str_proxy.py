from unittest import TestCase
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy


class StrProxyTestCase(TestCase):
    def test_proxy(self):
        self.assertEqual("foobar", StrProxy("foobar"))
        self.assertEqual(StrProxy("foobar"), StrProxy("foobar"))

    def test_meta(self):
        s = StrProxy("foobar")
        self.assertIsNone(s._meta.date)
        self.assertIsNone(s._meta.transformation)
        self.assertIsNone(s._meta.locale)

        new_s = StrProxy("foobar", meta={"locale": "uk"})
        self.assertEqual(new_s._meta.locale, "uk")

        even_newer_s = StrProxy(s, meta={"locale": "en"})
        self.assertEqual(even_newer_s._meta.locale, "en")

        supernova_s = StrProxy(
            even_newer_s, meta={"locale": "de", "transformation": "noop"}
        )
        self.assertEqual(even_newer_s._meta.locale, "en")
        self.assertIsNone(even_newer_s._meta.transformation, "en")
        self.assertEqual(supernova_s._meta.locale, "de")
        self.assertEqual(supernova_s._meta.transformation, "noop")

    def test_injection(self):
        s = StrProxy("foobar", meta={"locale": "uk"})
        traditional_s = "barfoo"
        better_s = s.inject_meta_to_str(traditional_s)

        self.assertEqual(better_s, "barfoo")
        self.assertEqual(better_s._meta.locale, "uk")

        even_better_s = StrProxy("double_bar", meta={"locale": "en"})
        self.assertEqual(even_better_s._meta.locale, "en")
        ultimate_s = better_s.inject_meta_to_str(even_better_s)
        self.assertEqual(ultimate_s._meta.locale, "uk")
        self.assertEqual(ultimate_s, "double_bar")

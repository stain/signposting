"""Test the linkheader parsing."""

import unittest

from signposting import linkheader
from httplink import parse_link_header

def _first(iterable):
    for v in iterable:
        return v
    raise KeyError("Iterable is empty")

class TestFilterLinks(unittest.TestCase):
    parsedLinks = parse_link_header("""
    <http://example.com/alternate>;rel=alternate,
    <http://example.com/author1>;rel=author,
    <http://example.com/author2>;rel=author,
    <http://example.com/canonical>;rel=canonical,
    <http://example.com/license>;rel=license
        """)

    def test_filter_multiple(self):
        filtered = linkheader._filter_links_by_rel(
            self.parsedLinks, "author", "cite-as")
        self.assertEqual("http://example.com/author1", filtered[0].target)
        self.assertEqual("http://example.com/author2", filtered[1].target)
        self.assertEqual(2, len(filtered))  # non-signposting rels ignored

    def test_filter_none_found(self):
        filtered = linkheader._filter_links_by_rel(self.parsedLinks, "cite-as", "type")
        self.assertEqual([], filtered)  # None found

    def test_filter_all_signposting(self):
        filtered = linkheader._filter_links_by_rel(self.parsedLinks)
        self.assertEqual("http://example.com/author1", filtered[0].target)
        self.assertEqual("http://example.com/author2", filtered[1].target)
        self.assertEqual("http://example.com/license", filtered[2].target)
        self.assertEqual(3, len(filtered))  # non-signposting rels ignored

    def test_invalid_rel_fails(self):
        with self.assertRaises(ValueError):
            linkheader._filter_links_by_rel(self.parsedLinks, "cite-as", "invalid")


class TestOptionalLink(unittest.TestCase):
    parsedLinks = parse_link_header("""
    <http://example.com/alternate>;rel=alternate,
    <http://example.com/canonical>;rel=canonical,
    <http://example.com/license>;rel=license
        """)

    def test_optional_link(self):
        self.assertEqual(linkheader._optional_link(self.parsedLinks, "license").target,
                         "http://example.com/license")
        self.assertEqual(linkheader._optional_link(self.parsedLinks, "LICENSE").target,
                         "http://example.com/license")
        self.assertIsNone(linkheader._optional_link(self.parsedLinks, "cite-as"))

    def test_invalid_rel_fails(self):
        with self.assertRaises(ValueError):
            linkheader._optional_link(self.parsedLinks, "alternate")


class TestAbsoluteAttribute(unittest.TestCase):
    def test_ANCHOR_upper_relative(self):
        self.assertEqual(("ANCHOR", "http://example.org/nested/example"),
                         linkheader._absolute_attribute("ANCHOR", "example", "http://example.org/nested/test"))

    def test_anchor_relative(self):
        self.assertEqual(("anchor", "http://example.org/nested/example"),
                         linkheader._absolute_attribute("anchor", "example", "http://example.org/nested/test"))

    def test_anchor_relative_root(self):
        self.assertEqual(("anchor", "http://example.org/example"),
                         linkheader._absolute_attribute("anchor", "/example", "http://example.org/nested/test"))

    def test_anchor_absolute(self):
        self.assertEqual(("anchor", "http://example.com/already-absolute"),
                         linkheader._absolute_attribute("anchor", "http://example.com/already-absolute", "http://example.org/nested/test"))

    def test_not_anchor(self):
        self.assertEqual(("not-anchor", "/untouched"),
                         linkheader._absolute_attribute("not-anchor", "/untouched", "http://example.org/nested/test"))


class TestSignposting(unittest.TestCase):

    signposting = parse_link_header("""
    <http://example.com/author1>;rel=author,
    <http://example.com/author2>;rel=author,
    <http://example.com/alternate>;rel=alternate;type="appliation/pdf",
    <http://example.com/metadata1>;rel=describedby;type="text/turtle",
    <http://example.com/license>;rel=license,
    <http://example.com/type1>;rel=type,
    <http://example.com/item1>;rel=item,
    <http://example.com/type2>;rel=type,
    <http://example.com/item2>;rel=item,
    <http://example.com/cite-as>;rel=cite-as
        """)

    noSignposting = parse_link_header("""
    <http://example.com/alternate>;rel=alternate;type="appliation/pdf"
        """)

    def test_signposting(self):
        s = linkheader.Signposting(self.signposting, "http://example.com/")

        self.assertEqual({a.target for a in s.authors},
                         {"http://example.com/author1", "http://example.com/author2"})
        self.assertEqual({d.target for d in s.describedBy},
                         {"http://example.com/metadata1"})
        self.assertEqual({d.type for d in s.describedBy},
                         {"text/turtle"})  # attributes preserved
        self.assertEqual(s.license.target,
                         "http://example.com/license")
        self.assertEqual(s.citeAs.target,
                         "http://example.com/cite-as")
        self.assertEqual({t.target for t in s.types},
                         {"http://example.com/type1", "http://example.com/type2"})
        self.assertEqual({i.target for i in s.items},
                         {"http://example.com/item1", "http://example.com/item2"})
        self.assertIsNone(s.collection)

    def test_nosignposting(self):
        s = linkheader.Signposting("http://example.com/", self.noSignposting)
        self.assertEqual(set(), s.authors)
        self.assertEqual(set(), s.describedBy)
        self.assertEqual(set(), s.types)
        self.assertEqual(set(), s.items)
        self.assertIsNone(s.license)
        self.assertIsNone(s.citeAs)
        self.assertIsNone(s.collection)


class TestFindSignposting(unittest.TestCase):
    def test_find_signposting_no_headers(self):
        s = linkheader.find_signposting([])
        self.assertEqual(set(), s.authors)
        self.assertEqual(set(), s.describedBy)
        self.assertEqual(set(), s.types)
        self.assertEqual(set(), s.items)
        self.assertIsNone(s.license)
        self.assertIsNone(s.citeAs)
        self.assertIsNone(s.collection)
        # TODO: Add a isFAIR() test?

    absolute_headers = [
        '<http://example.com/author1>;rel=author',
        '<http://example.com/author2>;rel=author',
        '<http://example.com/alternate>;rel=alternate;type="appliation/pdf"',
        '<http://example.com/metadata1>;rel=describedby;type="text/turtle"',
        '<http://example.com/license>;rel=license',
        '<http://example.com/type1>;rel=type',
        '<http://example.com/item1>;rel=item',
        '<http://example.com/type2>;rel=TYPE',  # deliberate upper-case and out of order
        '<http://example.com/item2>;rel=ITEM',  # ..still equivalent relations as above
        '<http://example.com/cite-as>;rel=cite-as',
        ]

    def test_find_signposting_absolute(self):
        s = linkheader.find_signposting(self.absolute_headers)
        self.assertEqual({a.target for a in s.authors},
                         {"http://example.com/author1", "http://example.com/author2"})
        self.assertEqual({d.target for d in s.describedBy},
                         {"http://example.com/metadata1"})
        self.assertEqual(s.license.target,
                         "http://example.com/license")
        self.assertEqual({t.target for t in s.types},
                         {"http://example.com/type1", "http://example.com/type2"})
        self.assertEqual({i.target for i in s.items},
                         {"http://example.com/item1", "http://example.com/item2"})
        self.assertEqual(s.citeAs.target,
                         "http://example.com/cite-as")
        self.assertIsNone(s.collection)

    relative_headers = [
        '<author1>;rel=author',
        '</author2>;rel=author',
        '<http://example.com/alternate>;rel=alternate;type="appliation/pdf"',  # ignored
        '<./metadata1>;rel=describedby;type="text/turtle"',
        '</license>;rel=license',
        '<http://example.com/type1>;rel=type',
        '<../type2>;rel=type',
        '<item1>;rel=item',
        '<http://example.com/cite-as>;rel=cite-as'
        ]

    def test_find_signposting_relative(self):
        s = linkheader.find_signposting(self.relative_headers,
                                "http://example.org/nested/")
        self.assertEqual({a.target for a in s.authors},
                         {"http://example.org/nested/author1",
                          "http://example.org/author2"})
        self.assertEqual({d.target for d in s.describedBy},
                         {"http://example.org/nested/metadata1"})
        self.assertEqual({d.type for d in s.describedBy},
                         {"text/turtle"})  # attributes preserved
        self.assertEqual(s.license.target, "http://example.org/license")
        self.assertEqual({t.target for t in s.types},
                         {"http://example.com/type1", "http://example.org/type2"})
        self.assertEqual({i.target for i in s.items},
                         {"http://example.org/nested/item1"})
        self.assertEqual(s.citeAs.target, "http://example.com/cite-as")
        self.assertIsNone(s.collection)

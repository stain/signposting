"""Test the linkheader parsing."""

import unittest

from signposting import linkheader as LH
from httplink import parse_link_header


class TestFilterLinks(unittest.TestCase):

    parsedLinks = parse_link_header("""
    <http://example.com/alternate>;rel=alternate,
    <http://example.com/author>;rel=author,
    <http://example.com/canonical>;rel=canonical,
    <http://example.com/license>;rel=license
        """)

    def test_filter_links_by_rel(self):    
        filtered = LH._filter_links_by_rel(self.parsedLinks, *LH.SIGNPOSTING)        
        self.assertEqual("http://example.com/author", filtered[0].target)
        self.assertEqual("http://example.com/license", filtered[1].target)
        self.assertEqual(2, len(filtered)) # non-signposting rels ignored

class TestSignposting(unittest.TestCase):


    parsedLinks = parse_link_header("""
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

    def test_constructor(self):
        s = LH.Signposting(self.parsedLinks)
        self.assertEqual(["http://example.com/author1", "http://example.com/author2"], 
            [a.target for a in s.author])
        self.assertEqual(["http://example.com/metadata1"], 
            [d.target for d in s.describedBy])            
        self.assertEqual("http://example.com/license", s.license.target)
        self.assertEqual("http://example.com/cite-as", s.citeAs.target)
        self.assertEqual(["http://example.com/type1", "http://example.com/type2"], 
            [t.target for t in s.type])
        self.assertEqual(["http://example.com/item1", "http://example.com/item2"], 
            [i.target for i in s.item])
        self.assertIsNone(s.collection)


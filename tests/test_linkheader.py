"""Test the linkheader parsing."""


from signposting import linkheader as LH
from httplink import parse_link_header

def test_filter_links_by_rel():    
    parsedlinks = parse_link_header("""
<http://example.com/alternate>;rel=alternate,
<http://example.com/author>;rel=author,
<http://example.com/alternate>;rel=alternate,
<http://example.com/license>;rel=license
    """)    
    filtered = LH._filter_links_by_rel(parsedlinks.links, rels=LH.SIGNPOSTING)
    assert filtered


"""Test the linkheader parsing."""

from signposting import linkheader as LH

from sampleproject.libs import samplemodule as SM

from httplink import Link

def test_filter_links_by_rel():    
    links = parse_link_header("""
<http://example.com/alternate>;rel=alternate,
<http://example.com/author>;rel=author,
<http://example.com/alternate>;rel=alternate
<http://example.com/license>;rel=license,
    """)    
    filtered = LH._filter_links_by_rel(links, LH.SIGNPOSTING)
    assert filtered


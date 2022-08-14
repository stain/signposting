#   Copyright 2022 The University of Manchester, UK
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Parse HTML to find <link> elements for signposting.
"""

from html.parser import HTMLParser
from io import FileIO
from typing import Tuple, Union
import warnings
import requests
from bs4 import BeautifulSoup,SoupStrainer
from .signpost import SIGNPOSTING,AbsoluteURI,Signpost,Signposting

def find_signposting_html(uri:Union[AbsoluteURI, str]) -> Signposting:
    """Parse HTML to find <link> elements for signposting.
    
    HTTP redirects will be followed and any relative paths in links
    made absolute correspondingly.

    :param uri: An absolute http/https URI, which HTML will be inspected.
    :throws ValueError: If the `uri` is invalid
    :throws IOError: If the network request failed, e.g. connection timeout
    :throws requests.HTTPError: If the HTTP request failed, e.g. 404 Not Found
    :throws UnrecognizedContentType: If the HTTP resource was not a recognized HTML/XHTML content type
    :throws HTMLParser.HTMLParseError: If the HTML could not be parsed.
    :returns: A parsed `Signposting` object (which may be empty)
    """
    html = _get_html(AbsoluteURI(uri))
    return _parse_html(html)

class DownloadedText(str):
    """Text downloaded from HTTP"""

    content_type: str
    """The returned Content-Type of the downloaded text"""

    requested_url: AbsoluteURI
    """The requested URL, before redirection"""

    resolved_url: AbsoluteURI
    """The resolved URL, after redirection and observing any Content-Location header."""

    def __new__(cls, value:str, content_type:str, requested_url:AbsoluteURI, resolved_url:AbsoluteURI):
        # NOTE: Do not return value if it's already an DownloadedText
        # instance; it may differ in the other attributes or subclass
        s = super().__new__(cls, value)
        # NOTE: content_type is necessarily a signpost.MediaType, 
        # as this string typically include charset, e.g. 
        # "text/html; charset=iso-8859-1"
        s.content_type = content_type
        s.requested_url = requested_url
        s.resolved_url = resolved_url
        return s

class HTML(DownloadedText):
    """Downloaded HTML document as string"""
    pass

class XHTML(DownloadedText):
    """Downloaded XHTML document as a string"""
    pass

class UnrecognizedContentType(Exception):
    def __init__(self, content_type:str, uri:AbsoluteURI):
        super().__init__("Unrecognized content-type %s for <%s>" % (content_type, uri))
        self.content_type = content_type
        self.uri = uri

def _get_html(uri:AbsoluteURI) -> Union[HTML,XHTML]:
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"
    }
    # Should ideally throw Not Acceptable error if none of the above
    page = requests.get(uri, headers=HEADERS)

    resolved_url = AbsoluteURI(page.url, uri)
    if "Content-Location" in page.headers:
        # More specific, e.g. "index.en.html" - parse as relative URI reference
        resolved_url = AbsoluteURI(page.headers["Content-Location"], resolved_url)

    if page.status_code == 203:
        warnings.warn("203 Non-Authoritative Information <%s> - Signposting URIs may have been rewritten by proxy" %
                    resolved_url)
    elif page.status_code == 410:
            warnings.warn(
                "410 Gone <%s> - still processing signposting for thumbstone page" % resolved_url)
    else:
        # raise requests.HTTPError for any other 4xx/5xx error
        page.raise_for_status()
    
    ct = page.headers.get("Content-Type", "")
    if "text/html" in ct:
        # page.text should get HTTP-level encoding correct,
        # but will not know about any charset declarations inside.
        return HTML(page.text, ct, uri, resolved_url)
    elif "application/xhtml+xml" in ct or "application/xml" in ct or "xhtml" in ct or "+xml" in ct:
        # Hopefully some XHTML inside.
        # These typically don't have charset parameter, the below
        # will guess by detection
        return XHTML(page.text, ct, uri, resolved_url)
    else:
        # HTTP server didn't honor our Accept header, and returned non-HTML.
        # It may be an image or something else that will crash our HTML parser,
        # so we'll bail out here.
        raise UnrecognizedContentType(ct, uri)

def _parse_html(html:Union[HTML,XHTML]) -> Signposting:
    soup = BeautifulSoup(html, 'html.parser', 
        # Ignore any other elements to reduce chance of parse errors
        parse_only=SoupStrainer(["head", "link"]))
    signposts = []
    if soup.head: # In case <head> was missing
        for link in soup.head.find_all("link"):
            # Ensure all filters are in lower case and known
            url = link.get("href")
            if not url:
                warnings.warn("Invalid <link> element, missing href attribute: %s" % link)
                continue
            type = link.get("type")
            profiles = link.get("profile")
            rels = set(r.lower() for r in link.get("rel", [])
                        if r.lower() in SIGNPOSTING)
            for rel in rels:
                try:
                    signpost = Signpost(rel, url, type, profiles, html.resolved_url)
                except ValueError as e:
                    warnings.warn("Ignoring invalid signpost from %s: %s" % (html.requested_url, e))
                    continue
                signposts.append(signpost)
    if not signposts:
        warnings.warn("No signposting found from <%s>" % html.requested_url)
    return Signposting(html.resolved_url, signposts)

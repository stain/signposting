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
from typing import Union
import warnings
import requests
from bs4 import BeautifulSoup,SoupStrainer
from .signpost import SIGNPOSTING,AbsoluteURI,Signpost,Signposting

def find_signposting_html(uri:Union[AbsoluteURI, str]) -> Signposting:
    """Parse HTML to find <link> elements for signposting.
    
    HTTP redirects will be followed.

    :param uri: An absolute http/https URI, which HTML will be inspected.
    :throws ValueError: If the `uri` is invalid
    :throws IOError: If the network request failed, e.g. connection timeout
    :throws requests.HTTPError: If the HTTP request failed, e.g. 404 Not Found
    :throws HTMLParser.HTMLParseError: If the HTML could not be parsed.
    :returns: A parsed `Signposting` object (which may be empty)
    """
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"
    }
    page = requests.get(AbsoluteURI(uri), headers=HEADERS)
    context = page.url
    if page.status_code == 203:
        warnings.warn("203 Non-Authoritative Information <%s> - Signposting URIs may have been rewritten by proxy" %
                    context)
    elif page.status_code == 410:
            warnings.warn(
                "410 Gone <%s> - still processing signposting for thumbstone page" % context)
    else:
        # raise requests.HTTPError for any other 4xx/5xx error
        page.raise_for_status()
    
    ct = page.headers["Content-Type"]
    if not "text/html" in ct or "application/xhtml+xml" in ct or "application/xml" in ct or "+xml" in ct:
        warnings.warn("Unrecognised media type %s for <%s>, skipping HTML parsing" % (ct, uri))
        return Signposting(context) # empty

    soup = BeautifulSoup(page.content, 'html.parser', 
        # Ignore any other elements to reduce chance of parse errors
        parse_only=SoupStrainer(["head", "link"]))
    signposts = []
    if soup.head: # In case <head> was missing
        for link in soup.head.find_all("link"):
            # Ensure all filters are in lower case and known
            url = link.get("href")
            if not url:
                continue
            type = link.get("type")
            profiles = link.get("profile")
            rels = set(r.lower() for r in link.get("rel", [])
                        if r.lower() in SIGNPOSTING)
            for rel in rels:
                try:
                    signpost = Signpost(rel, url, type, profiles, context)
                except ValueError as e:
                    warnings.warn("Ignoring invalid signpost from %s: %s" % (uri, e))
                    continue
                signposts.append(signpost)
    if not signposts:
        warnings.warn("No signposting found: %s" % uri)
    return Signposting(context, signposts)

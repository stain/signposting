#   Copyright 2022 Stian Soiland-Reyes
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
Parse HTTP headers to find Signposting links
"""

from typing import Dict, List, Set, Tuple, Optional, Collection, Set
import httplink
from httplink import ParsedLinks, Link, parse_link_header
from urllib.parse import urljoin

# Only relations listed below will be selected
# Sources:
#   https://signposting.org/conventions/
#   https://signposting.org/FAIR/
"""Valid Signposting link relations"""
SIGNPOSTING=set("author collection describedby describes item cite-as type license linkset".split(" "))

def _filter_links_by_rel(parsedLinks:ParsedLinks, *rels:str) -> List[Link]:
    if rels:        
        # Ensure all filters are in lower case
        filterRels = set(r.lower() for r in rels)
        unknown = filterRels - SIGNPOSTING
        if unknown:
            raise ValueError("Unknown FAIR Signposting relations: %s" % unknown)
    else:
        # Fallback - all valid signposting relations
        filterRels = SIGNPOSTING
    return [l for l in parsedLinks.links if l.rel & filterRels]

def _optional_link(parsedLinks:ParsedLinks, rel:str) -> Optional[Link]:
    if not rel.lower() in SIGNPOSTING:
        raise ValueError("Unknown FAIR Signposting relation: %s" % rel)
    if rel in parsedLinks:
        return parsedLinks[rel]
    return None


class Signposting:
    """Signposting links for a given resource.
    
    Links are discovered according to `FAIR`_ `signposting`_ conventions.

    .. _signposting: https://signposting.org/conventions/
    .. _FAIR: https://signposting.org/FAIR/
    """

    """Resource URL this is the signposting for, e.g. a HTML landing page"""
    context_url: str

    """Author(s) of the resource (and presuambly it items)"""
    author: List[Link]

    """Metadata resources about the resource and its items, typically in a Linked Data format. 
    
    Resources may require content negotiation, check ``Link["type"]`` attribute
    (if present) for content type, e.g. ``text/turtle``.
    """
    describedBy: List[Link]

    """Semantic types of the resource, e.g. from schema.org"""
    type: List[Link]

    """Items contained by this resource, e.g. downloads.
    
    The content type of the download may be available as ``Link["type"]``` attribute.
    """
    item: List[Link]

    """Linkset resuorces with further signposting.

    A `linkset`_ is a JSON or text serialization of Link headers available as a
    separate resource, and may be used to externalize large collection of links, e.g.
    thousands of "item" relations.

    Resources may require content negotiation, check ``Link["type"]`` attribute
    (if present)  for content types ``application/linkset`` or ``application/linkset+json``.

    .. _linkset: https://datatracker.ietf.org/doc/draft-ietf-httpapi-linkset/
    """
    linkset: List[Link]

    """Persistent Identifier (PID) for this resource, preferred for citation and permalinks"""
    citeAs: Optional[Link]

    """Optional license of this resource (and presumably its items)"""
    license: Optional[Link]
    
    """Optional collection this resource is part of"""
    collection: Optional[Link]

    def __init__(self, parsedLinks:ParsedLinks, context_url:str):
        # According to FAIR Signposting
        # <https://www.signposting.org/FAIR/> version 20220225
        self.context_url = context_url
        self.author = _filter_links_by_rel(parsedLinks, "author")
        self.describedBy = _filter_links_by_rel(parsedLinks, "describedby")
        self.type = _filter_links_by_rel(parsedLinks, "type")
        self.item = _filter_links_by_rel(parsedLinks, "item")
        self.linkset =  _filter_links_by_rel(parsedLinks, "linkset")
        self.citeAs = _optional_link(parsedLinks, "cite-as")
        self.license = _optional_link(parsedLinks, "license")
        self.collection = _optional_link(parsedLinks, "collection")

def _absolute_attribute(k:str, v:str, baseurl:str) -> Tuple[str,str]:
    """Ensure link attributes 
    """
    if k.lower() == "anchor":
        return k, urljoin(baseurl, v)
    return k, v

def find_signposting(headers:List[str], baseurl:str=None) -> Signposting:
    """Find signposting among HTTP Link headers. 

    Optionally make the links absolute according to the base URL.

    The link headers should be valid according to `RFC8288`_, excluding the "Link:" prefix.
    
    Links are discovered according to defined `FAIR`_ `signposting`_ relations.

    .. _signposting: https://signposting.org/conventions/
    .. _FAIR: https://signposting.org/FAIR/
    .. _rfc8288: https://doi.org/10.17487/RFC8288
    
    """
    parsed = parse_link_header(", ".join(headers))
    signposting: List[Link] = []
    # Ignore non-Signposting relations like "stylesheet"
    for l in _filter_links_by_rel(parsed):
        if baseurl is not None:
            # Make URLs absolute by modifying Link object in-place
            target = urljoin(baseurl, l.target)
            attributes = [_absolute_attribute(k,v, baseurl) for k,v in l.attributes]            
            link = Link(target, attributes)
        else:
            link = l # unchanged
        signposting.append(link)
    return Signposting(ParsedLinks(signposting), baseurl)

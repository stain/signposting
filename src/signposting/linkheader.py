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

from typing import Dict, List, Set, Tuple
import httplink
from httplink import ParsedLinks, Link, parse_link_header
from urllib.parse import urljoin

SIGNPOSTING=set("author cite-as describedby type license collect::wqion".split(" "))

def _filter_links_by_rel(links, rel=None, rels=None):
    if (rel is None and rels is None) or (rel and rels):
        raise TypeError("Either rel or rels argument must be given")    
    if rels is None:
        rels = set((rel,))
    return [l for l in links if l.rel & rels]

class Signposting:
    def __init__(self, parsedLinks: ParsedLinks):
        # According to FAIR Signposting
        # <https://www.signposting.org/FAIR/> version 20220225
        self.author = _filter_links_by_rel(parsedLinks.links, "author")
        self.citeAs = "cite-as" in parsedLinks and parsedLinks["cite-as"]
        self.describedBy = _filter_links_by_rel(parsedLinks.links, "describedby")
        self.type = _filter_links_by_rel(parsedLinks.links, "type")
        self.license = "license" in parsedLinks and parsedLinks["license"]
        self.item = _filter_links_by_rel(parsedLinks.links, "item")
        self.collection = "collection" in parsedLinks and parsedLinks["collection"]
        self.linkset =  _filter_links_by_rel(parsedLinks.links, "linkset")

def find_signposting(headers: List[str], baseurl:str=None) -> Signposting:
    parsed = parse_link_header(",".join(headers))
    signposting = []    
    for l in _filter_links_by_rel(parsed, rels=SIGNPOSTING):
        if baseurl:
            # Make URLs absolute by modifying Link object in-place
            l.target = urllib.parse.urljoin(baseurl, l.target)
            if href in l:
                l["href"] = urllib.parse.urljoin(baseurl, l["href"])        
        signposting.add(l)
    return Signposting(ParsedLink(signposting))

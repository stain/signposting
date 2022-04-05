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

SIGNPOSTING=set("author cite-as describedby type license collect::wqion".split(" "))

def _filter_links_by_rel(parsedLinks:ParsedLinks, *rels:str) -> List[Link]:    
    return [l for l in parsedLinks.links if l.rel & set(rels)]

def _optional_link(parsedLinks:ParsedLinks, rel:str) -> Optional[Link]:
    if rel in parsedLinks:
        return parsedLinks[rel]
    return None



class Signposting:    
    author: List[Link]
    describedBy: List[Link]
    type: List[Link]
    item: List[Link]
    linkset: List[Link]
    citeAs: Optional[Link]
    license: Optional[Link]
    collection: Optional[Link]

    def __init__(self, parsedLinks:ParsedLinks):
        # According to FAIR Signposting
        # <https://www.signposting.org/FAIR/> version 20220225
        self.author = _filter_links_by_rel(parsedLinks, "author")
        self.describedBy = _filter_links_by_rel(parsedLinks, "describedby")
        self.type = _filter_links_by_rel(parsedLinks, "type")
        self.item = _filter_links_by_rel(parsedLinks, "item")
        self.linkset =  _filter_links_by_rel(parsedLinks, "linkset")
        self.citeAs = _optional_link(parsedLinks, "cite-as")
        self.license = _optional_link(parsedLinks, "license")
        self.collection = _optional_link(parsedLinks, "collection")

def _absolute_attribute(k:str,v:str, baseurl:str) -> Tuple[str,str]:
    if k.lower() == "href":
        return k, urljoin(baseurl, v)
    return k, v

def find_signposting(headers:List[str], baseurl:str=None) -> Signposting:
    parsed = parse_link_header(",".join(headers))
    signposting: List[Link] = []    
    for l in _filter_links_by_rel(parsed, *SIGNPOSTING):
        if baseurl is not None:
            # Make URLs absolute by modifying Link object in-place
            target = urljoin(baseurl, l.target)
            attributes = [_absolute_attribute(k,v, baseurl) for k,v in l.attributes]            
            link = Link(target, attributes)
        else:
            link = l
        signposting.append(link)
    return Signposting(ParsedLinks(signposting))

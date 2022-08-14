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
Parse linkset documents (`RFC9264`_) for signposting.

.. _RFC9264: https://www.rfc-editor.org/rfc/rfc9264.html
"""

from typing import List, Tuple, Union
import warnings
import requests
import json
import httplink
from .signpost import SIGNPOSTING,AbsoluteURI,Signpost,Signposting,MediaType
from .htmllinks import DownloadedText,UnrecognizedContentType
from .linkheader import find_signposting_http_link

def find_signposting_linkset(uri:Union[AbsoluteURI, str], acceptType:Union[MediaType, str]=None) -> Signposting:
    """Parse linkset to find <link> elements for signposting.
    
    HTTP redirects will be followed.

    :param uri: An absolute http/https URI, which HTML will be inspected.
    :param acceptType: A `MediaType` to content-negotiate access for. 
        The default is to content-negotiate including ``application/linkset`` and 
        ``application/linkset+json`` with JSON having preference.
    :throws ValueError: If the `uri` is invalid
    :throws IOError: If the network request failed, e.g. connection timeout
    :throws requests.HTTPError: If the HTTP request failed, e.g. 404 Not Found
    :throws UnrecognizedContentType: If the HTTP resource was not a recognized linkset content type. 
        This exception is also raised if ``acceptType`` was provided, 
        but didn't match returned ``Content-Type``.
    :throws HTMLParser.HTMLParseError: If the HTML could not be parsed.
    :returns: A parsed `Signposting` object (which may be empty)
    """
    if acceptType:
        linkset = _get_linkset(AbsoluteURI(uri), MediaType(acceptType))
    else:
        linkset = _get_linkset(AbsoluteURI(uri))

    if isinstance(linkset, LinksetJSON):
        return _parse_linkset_json(linkset)
    else:
        return _parse_linkset(linkset)

class LinksetJSON(DownloadedText):
    """Downloaded application/linkset+json document as string"""
    pass

class Linkset(DownloadedText):
    """Downloaded application/linkset document as a string"""
    pass

DEFAULT_ACCEPT = "application/linkset+json,application/linkset;q=0.9,application/json;q=0.3,text/plain;q=0.2"

def _get_linkset(uri:AbsoluteURI, acceptType:MediaType=None) -> Union[LinksetJSON,Linkset]:
    header = {
        "Accept": acceptType and str(acceptType) or DEFAULT_ACCEPT
    }
    # Should ideally throw Not Acceptable error if none of the above
    page = requests.get(uri, headers=header)

    resolved_url = AbsoluteURI(page.url, uri)
    if "Content-Location" in page.headers:
        # More specific, e.g. "index.en.html" - parse as relative URI reference
        resolved_url = AbsoluteURI(page.headers["Content-Location"], resolved_url)

    if page.status_code == 203:
        warnings.warn("203 Non-Authoritative Information <%s> - Signposting URIs may have been rewritten by proxy" %
                    resolved_url)
    # raise requests.HTTPError for any other 4xx/5xx error
    page.raise_for_status()
    
    ct = page.headers.get("Content-Type", "")
    if acceptType and not acceptType in ct:
        # mismatch from what we requested explicitly
        raise UnrecognizedContentType(ct, uri)    
    elif "application/linkset+json" in ct or "json" in ct:
        return LinksetJSON(page.text, ct, uri, resolved_url)
    elif "application/linkset" in ct or "text/plain" in ct:
        # NOTE: we covered linkset+json above, which would otherwise also match here
        return Linkset(page.text, ct, uri, resolved_url)
    else:
        # HTTP server didn't honor our default Accept header, we'll bail out here.
        raise UnrecognizedContentType(ct, uri)    

def _parse_linkset(linkset:Linkset) -> Signposting:
    # RFC9264 is based on RFC8288 but also permits newlines.
    # We'll lazily replace them with accepted whitespace:
    link = linkset.replace("\r", " ").replace("\n", " ").strip()
    return find_signposting_http_link([link], linkset.resolved_url)
    # TODO: Filter away links that do not have the desired context?

def _parse_linkset_json(linkset:LinksetJSON) -> Signposting:
    linksetJSON = json.loads(linkset)
    if not "linkset" in linksetJSON or not isinstance(linksetJSON["linkset"], list):
        raise ValueError("Not a valid RFC9264 JSON, top list 'linkset' required")
    signposts: List[Signpost] = []
    for link_context in linksetJSON["linkset"]:
        if "anchor" in link_context:
            anchor = AbsoluteURI(link_context["anchor"], linkset.resolved_url)
        else:
            # The linkset itself
            anchor = linkset.resolved_url
        for rel in link_context:
            if rel == "anchor": 
                # Not a link relation, handled above
                continue
            if not rel in SIGNPOSTING:
                # Not a signposting relation, ignored
                continue
            # Proceed to find signposts
            if not isinstance(link_context[rel], list):
                warnings.warn("Not an array, ignoring link targets for rel=%s" % rel)
                continue
            for link_target in link_context[rel]:
                if not "href" in link_target:
                    warnings.warn("Missing required 'href' attribute, ignoring link target for rel=%s" % rel)
                    continue
                href = link_target["href"]
                type = link_target.get("type")
                profile = link_target.get("profile")
                # Signposting ignores the other attributes for now. 
                # TODO: parse them into a Link object for equivalence with
                # _parse_linkset() 
                s = Signpost(rel, href, type, profile, anchor)
                signposts.append(s)
    if not signposts:
        warnings.warn("No signposts found: <%s>" % linkset.requested_url)
    return Signposting(linkset.resolved_url, signposts)

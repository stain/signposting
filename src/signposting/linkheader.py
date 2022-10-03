# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2022 Stian Soiland-Reyes
#
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

from typing import List, Tuple, Optional
from httplink import ParsedLinks, Link, parse_link_header
from urllib.parse import urljoin
from .signpost import SIGNPOSTING, Signpost, Signposting, LinkRel


def _filter_links_by_rel(parsedLinks: ParsedLinks, *rels: str) -> List[Link]:
    """Filter links to select from a set of relations.

    The relations must be valid Signposting relation listed in `SIGNPOSTING`.

    :param parsedLinks: The :class:`ParsedLinks` to filter from
    :param rels: One or more link relations to filter by, e.g. ``item``
    :return: A list of :class:`Link` which ``rel`` match the given `rels`.

    """
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


def _optional_link(parsedLinks: ParsedLinks, rel: str) -> Optional[Link]:
    """Look up a single link relation.

    The relation must be a valid Signposting relation listed in `SIGNPOSTING`.

    It is undefined which relation is returned if multiple links of the same
    relation are found.

    :param parsedLinks: The :class:`ParsedLinks` to look up from
    :param rel: The link relation to look up by, e.g. ``author``
    :return: The found ``Link``, or ``None`` if not found.
    """
    if not rel.lower() in SIGNPOSTING:
        raise ValueError("Unknown FAIR Signposting relation: %s" % rel)
    if rel in parsedLinks:
        return parsedLinks[rel]
    return None

def _link_attr(link: Link, key: str) -> Optional[str]:
    """Look up an optional link attribute with given `key` from a `Link`.

    This is a workaround as :class:`Link` exposes ``__getitem__`` and ``__contains__`` but not ``Dict.get()``

    :param link: :class:`Link` to look up attribute of
    :param key: Link attribute key to look up
    :return: The attribute value, or ``None`` if the link attribute was not found.
    """
    if key in link:
        return link[key]
    return None

def linkToSignpost(link: Link, rel: LinkRel, context_url: str = None) -> Signpost:
    """Convert from a :class:`Link` to a :class:`Signpost` 
    object for a given link relation.

    :param link: The :class:`Link` to convert
    :param rel: The link relation to create a signpost for
    :param context_url: Optional, the context URL these link describe (unless specifying ``anchor``)
    :return: The converted :class:`Signpost` object
    """
    context = _link_attr(link, "anchor") or context_url
    return Signpost(rel, link.target,
        _link_attr(link, "type"),
        _link_attr(link, "profile"),
        context, link)

def linksToSignposting(links: List[Link], context: str = None) -> Signposting:
        """Initialize Signposting object for a given `ParsedLinks`
        as discovered from the (optional) `context` base URL.

        :param links: A list of :class:`Link` to convert
        :param context: Optional, the context URL these link describe (unless specifying ``anchor``)
        :return: The :class:`Signposting` of the converted :class:`Signpost` objects
        """
        signposts: List[Signpost] = []
        for l in links:
            # TODO: Check if context matches "anchor"
            for rel in l.rel:
                if rel in SIGNPOSTING:
                    signposts.append(linkToSignpost(l, LinkRel(rel), context))
        return Signposting(context, signposts)

def _absolute_attribute(k: str, v: str, baseurl: str) -> Tuple[str, str]:
    """Ensure link attribute value uses absolute URI, resolving from the baseurl.

    Currently this will mean the `context`_ attribute ``anchor``
    and ``profile`` will be rewritten.

    .. _context: https://datatracker.ietf.org/doc/html/rfc8288#section-3.2
    """
    if k.lower() == "anchor" or k.lower() == "profile":
        return k, urljoin(baseurl, v)
    return k, v


def find_signposting_http_link(headers: List[str], baseurl: str = None) -> Signposting:
    """Find signposting among HTTP Link headers.

    Links are discovered according to defined `FAIR`_ `signposting`_ relations.

    :param headers: A list of individual HTTP ``Link`` headers. 
        The headers should be valid according to `RFC8288`_, 
        excluding the ``"Link:"`` prefix.
    :param baseurl: Optional base URL to make relative link targets absolute from
    :return: A :class:`Signposting` of the collected signposts.

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
            attributes = [_absolute_attribute(
                k, v, baseurl) for k, v in l.attributes]
            link = Link(target, attributes)
        else:
            link = l  # unchanged
        signposting.append(link)
    return linksToSignposting(signposting, baseurl)

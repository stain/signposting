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
Representation of single Signpost link relation
"""

import re
from typing import Optional,Union,Set
from enum import Enum
from rdflib.term import URIRef
import rfc3987
import urllib.parse
from httplink import ParsedLinks, Link, parse_link_header
from warnings import warn

class AbsoluteURI(URIRef):
    """An absolute URI, e.g. "http://example.com/" """
    def __new__(cls, value: str, base: Optional[str] = None):
        """Create an absolute URI reference.
        
        If the base parameter is given, it is used to resolve the
        potentially relative URI reference, otherwise the first argument
        must be an absolute URI.

        This constructor will throw `ValueError` if the 
        final URI reference is invalid or not absolute.

        Note that IRIs are not supported.
        """
        uri = URIRef.__new__(cls, value, base)
        # below will throw ValueError if not valid
        rfc3987.parse(uri, rule="absolute_URI")
        return uri

    #@staticmethod
    #def from_iri(cls, value: str, base: Optional[str] = None):
    #    """https://stackoverflow.com/a/49620774"""
    #    iri = rfc3987.parse(uri, rule="absolute_IRI")
    #    netloc = iri["authority"] and iri["netloc"].encode('idna').decode('ascii')
    #    ## TODO: What about non-hostname schemes? 
    #    path = iri["path"] and urllib.parse.quote_from_bytes(iri['path'].encode('utf-8'))
    #    query = iri["query"] and urllib.parse.quote_from_bytes(iri['query'].encode('utf-8'))
    #    fragment = iri["fragment"] and urllib.parse.quote_from_bytes(iri['fragment'].encode('utf-8'))
    #   return ...

class MediaType(str):
    """An IANA media type, e.g. text/plain.

    This class ensures the type string is valid according to `RFC6838`_
    and for convenience converts it to lowercase.

    While the constructor do check that the main type is an offical IANA subtree
    (see `MediaType.MAIN`), it does not enforce the individual subtype to be registered.
    In particular RFC6838 permits unregistered subtypes 
    starting with `vnd.`, `prs.` and `x.`

    Extra content type parameters such as ``;profile=http://example.com/`` are 
    **not** supported by this class, as they do not form part of the 
    media type registration.

    .. _RFC6838: https://www.rfc-editor.org/rfc/rfc6838.html
    """
    
    """Top level type trees as of 2022-05-17 in `IANA`_ registry

    .. _IANA: https://www.iana.org/assignments/media-types/media-types.xhtml"""
    MAIN = "application audio example font image message model multipart text video".split()

    """Check the type string is valid following `section 4.2`_ of RFC6838.

     .. _section 4.2: https://www.rfc-editor.org/rfc/rfc6838.html#section-4.2
    """

    MAIN_SUB_RE = re.compile(r"""^
        ([a-z0-9] [a-z0-9!#$&^_-]*)
        /
        ([a-z0-9] [a-z0-9!#$&^_+.-]*)
        $""", re.VERBOSE)

    """The main type, e.g. image"""
    main: str 

    """The sub-type, e.g. jpeg"""
    sub: str

    def __new__(cls, value=str):
        """Construct a MediaType.
        
        Throws ValueError
        """
        if len(value) > 255:
            # Guard before giving large media type to regex
            raise ValueError("Media type should be less than 255 characters long")
        match = cls.MAIN_SUB_RE.match(value.lower())
        if not match:
            raise ValueError("Media type invalid according to RFC6838: {}".format(value))
        main,sub = match.groups()
        if len(main) > 127:
            raise ValueError("Media main type should be no more than 127 characters long")
        if len(sub) > 127:
            raise ValueError("Media sub-type should be no more than 127 characters long")
        if not main in cls.MAIN:
            warn("Unrecognized media type main tree: {}".format(main))
        # Ensure we use the matched string
        t = str.__new__(cls, match.group())
        t.main = main
        t.sub = sub
        return t

class LinkRel(Enum):
    """A link relation as used in Signposting.

    Link relations are defined by `RFC8288`_, but 
    only link relations listed in `FAIR`_ and `signposting`_ 
    conventions are included in this enumerator.

    .. _signposting: https://signposting.org/conventions/
    .. _FAIR: https://signposting.org/FAIR/
    .. RFC8288: https://datatracker.ietf.org/doc/html/rfc8288
    """
    author = "author"
    collection = "collection"
    describedby = "describedby"
    item = "item"
    cite_as = "cite-as" # NOTE: _ vs - because of Python syntax
    type = "type"
    license = "license"
    linkset = "linkset"

    def __repr__(self):
        return "rel=%s" % self.value

    def __str__(self):
        return self.value
    
SIGNPOSTING=set(LinkRel.__members__.keys())

class Signpost:
    """An individual link of Signposting, e.g. for rel=cite-as.
    
    This is a convenience class that may be wrapping a `Link`. 
    
    In some case the link relation may have additional attributes, 
    e.g. ``signpost.link["title"]`` - the purpose of this class is to 
    lift only the navigational attributes for FAIR Signposting.
    """

    """The link relation of this signposting"""
    rel : LinkRel

    """The URI that is the target of this link, e.g. "http://example.com/"
    
    Note that URIs with Unicode characters will be represented as %-escaped URIs.
    """
    target : AbsoluteURI

    """The media type of the target. 
    
    It is recommended to use this type in content-negotiation for
    retrieving the target URI.

    This property is optional, and should only be expected 
    if `rel` is `LinkRel.describedby` or `LinkRel.item`
    """
    ## TODO: Check RFC if this may also be a URI. 
    #type: Union[MediaType, AbsoluteURI]
    type: Optional[MediaType]

    """Profile URIs for the target with the given type.

    Profiles are mainly identifiers, indicating that a particular
    convention or subtype should be expected in the target's . 
    
    For instance, a ``rel=describedby`` signpost to a JSON-LD document can have
    ``type=application/ld+json`` and ``profile=http://www.w3.org/ns/json-ld#compacted``

    As there may be multiple profiles, or (more commonly) none, 
    this property is typed as a `Set`.
    """
    # FIXME: Correct JSON-LD profile
    profiles: Set[AbsoluteURI]

    """Resource URL this is the signposting for, e.g. a HTML landing page.    
    """
    context: Optional[AbsoluteURI]

    """The Link this signpost came from. 
    
    May contain additional attributes such as ``link["title"]``.
    Note that a single Link may have multiple ``rel``s, therefore it is
    possible that multiple `Signpost`s refer to the same link.
    """
    link: Optional[Link]

    def __init__(self, 
        rel:Union[LinkRel, str], 
        target:Union[AbsoluteURI, str], 
        media_type:Union[MediaType, str]=None,
        profiles:Union[Set[AbsoluteURI], str]=frozenset(),
        context:Union[AbsoluteURI, str]=None, 
        link:Link=None):
        """Construct a Signpost from a link relation.
        
        Required parameters:
        * ``rel`` (e.g. ``"cite-as"``)
        * ``target`` URI (e.g. ``"http://example.com/pid-01"``)

        Optionally include:
        * Expected ``media_type`` of the target (e.g. ``"text/html"``) 
        * The ``context`` URI this is a signposting from (e.g. ``"http://example.com/page-01.html"``) (called ``anchor`` in Link header)
        * Origin `Link` header (not parsed further) for further attributes

        This constructor will convert plain string values 
        to the corresponding type-checked 
        classes `LinkRel`, `AbsoluteURI`, `MediaType`,
        which may throw exception `ValueError` if they are 
        not valid. Alternatively, instances of these types can
        be provided directly.
        """
        
        if isinstance(rel, LinkRel):
            self.rel = rel
        else:
            try:
                self.rel = LinkRel[rel]
            except KeyError:
                raise ValueError("Unknown Signposting link relation {}".format(rel))
        
        if isinstance(target, AbsoluteURI):
            self.target = target
        else:
            self.target = AbsoluteURI(target) # may throw ValueError
        
        if isinstance(media_type, MediaType):
            self.type = media_type
        elif media_type:
            self.type = MediaType(media_type)
        else:
            self.type = None
        
        if isinstance(profiles, Set):
            for p in profiles:
                assert isinstance(p, AbsoluteURI)
            self.profiles = profiles
        else:            
            self.profiles = frozenset(AbsoluteURI(p) for p in profiles.split(" "))

        if isinstance(context, AbsoluteURI):
            self.context = context
        else:
            self.context = AbsoluteURI(context) # may throw ValueError

        self.link = link
    

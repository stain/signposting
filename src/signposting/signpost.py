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
Common types for describing signposting link relations:

* `Signposting` represent all the signposts for a given resource
* `Signpost` represent one particular signposting corresponding to a single link relation and single URI
* `LinkRel` enumerates signposting link relations
* `AbsoluteURI` represent an URI string
* `MediaType` represent an IANA media type string

These classes are general data holders, independent of the way
signposting links have been discovered or parsed. They would
be returned by methods like :meth:`find_signposting_http` 
or could be constructed manually for other purposes.

The main purpose of the typed strings is to ensure syntactic
validity at construction time, so that consumers of
`Signposting` objects can make strong assumptions
about type safety.
"""

import itertools
from multiprocessing import AuthenticationError
import re
from typing import Collection, Iterable, Iterator, List, Optional, Set, Sized, Union, AbstractSet, FrozenSet
from enum import Enum, auto, unique
import warnings

import rfc3987
import urllib.parse
from urllib.parse import urljoin
from httplink import Link
from warnings import warn


class AbsoluteURI(str):
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
        if isinstance(value, cls):
            return value # Already AbsoluteURI, no need to check again
        # Resolve potentially relative URI reference when base is given
        uri = urljoin(base or "", value)
        # will throw ValueError if resolved URI is not valid
        rfc3987.parse(uri, rule="absolute_URI")
        return super(AbsoluteURI, cls).__new__(cls, uri)

    # @staticmethod
    # def from_iri(cls, value: str, base: Optional[str] = None):
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

    MAIN = "application audio example font image message model multipart text video".split()
    """Top level type trees as of 2022-05-17 in `IANA`_ registry

    .. _IANA: https://www.iana.org/assignments/media-types/media-types.xhtml"""


    _MAIN_SUB_RE = re.compile(r"""^
        ([a-z0-9] [a-z0-9!#$&^_-]*)
        /
        ([a-z0-9] [a-z0-9!#$&^_+.-]*)
        $""", re.VERBOSE)
    """Check the type string is valid following `section 4.2`_ of RFC6838.

     .. _section 4.2: https://www.rfc-editor.org/rfc/rfc6838.html#section-4.2
    """

    main: str
    """The main type, e.g. image"""

    sub: str
    """The sub-type, e.g. jpeg"""

    def __new__(cls, value=str):
        """Construct a MediaType.

        Throws ValueError
        """
        if len(value) > 255:
            # Guard before giving large media type to regex
            raise ValueError(
                "Media type should be less than 255 characters long")
        match = cls._MAIN_SUB_RE.match(value.lower())
        if not match:
            raise ValueError(
                "Media type invalid according to RFC6838: {}".format(value))
        main, sub = match.groups()
        if len(main) > 127:
            raise ValueError(
                "Media main type should be no more than 127 characters long")
        if len(sub) > 127:
            raise ValueError(
                "Media sub-type should be no more than 127 characters long")
        if not main in cls.MAIN:
            warn("Unrecognized media type main tree: {}".format(main))
        # Ensure we use the matched string
        t = super(MediaType, cls).__new__(cls, match.group())
        t.main = main
        t.sub = sub
        return t


@unique
class LinkRel(str, Enum):
    """A link relation as used in Signposting.

    Link relations are defined by `RFC8288`_, but
    only link relations listed in `FAIR`_ and `signposting`_
    conventions are included in this enumerator.

    A link relation enum can be looked up from its RFC8288 _value_
    by calling ``LinkRel("cite-as")`` - note that this particular
    example has a different Python-compatible spelling in it's
    enum *name* (``LinkRel.cite_as``).

    .. _signposting: https://signposting.org/conventions/
    .. _FAIR: https://signposting.org/FAIR/
    .. RFC8288: https://datatracker.ietf.org/doc/html/rfc8288
    """
    author = "author"
    collection = "collection"
    describedby = "describedby"
    item = "item"
    cite_as = "cite-as"  # NOTE: _ vs - because of Python syntax
    type = "type"
    license = "license"
    linkset = "linkset"

    def __repr__(self):
        return "rel=%s" % self.value

    def __str__(self):
        return self.value


"""Signposting link relations as strings"""
SIGNPOSTING = set(l.value for l in LinkRel)

class Signpost:
    """An individual link of Signposting, e.g. for ``rel=cite-as``.

    This is a convenience class that may be wrapping a :attr:`link`. 

    In some case the link relation may have additional attributes,
    e.g. ``signpost.link["title"]`` - the purpose of this class is however to
    lift only the navigational attributes for FAIR Signposting.
    """

    rel: LinkRel
    """The link relation of this signposting"""

    target: AbsoluteURI
    """The URI that is the target of this link, e.g. ``http://example.com/``
    
    Note that URIs with Unicode characters will be represented as %-escaped URIs.
    """

    # TODO: Check RFC if this may also be a URI.
    type: Optional[MediaType]
    """The media type of the target.

    It is recommended to use this type in content-negotiation for
    retrieving the target URI.

    This property is optional, and should only be expected
    if `rel` is :const:`LinkRel.describedby` or :const:`LinkRel.item`
    """

    # FIXME: Correct JSON-LD profile
    profiles: FrozenSet[AbsoluteURI]
    """Profile URIs for the target with the given type.

    Profiles are mainly identifiers, indicating that a particular
    convention or subtype should be expected in the target's .

    For instance, a ``rel=describedby`` signpost to a JSON-LD document can have
    ``type=application/ld+json`` and ``profile=http://www.w3.org/ns/json-ld#compacted``

    As there may be multiple profiles, or (more commonly) none,
    this property is typed as a :class:`FrozenSet`.
    """

    context: Optional[AbsoluteURI]
    """Resource URL this is the signposting for, e.g. a HTML landing page.
    """

    link: Optional[Link]
    """The Link this signpost came from.

    May contain additional attributes such as ``link["title"]``.
    Note that a single Link may have multiple ``rel``s, therefore it is
    possible that multiple :class:`Signpost`s refer to the same link.
    """

    def __init__(self,
                 rel: Union[LinkRel, str],
                 target: Union[AbsoluteURI, str],
                 media_type: Union[MediaType, str] = None,
                 profiles: Union[AbstractSet[AbsoluteURI], str] = None,
                 context: Union[AbsoluteURI, str] = None,
                 link: Link = None):
        """Construct a Signpost from a link relation.

        :param rel: Link relation, e.g. ``"cite-as"``
        :param target: URI (e.g. ``"http://example.com/pid-01"``)
        :param media_type_: Optional expected media type of the target (e.g. ``"text/html"``)
        :param context: Optional URI this is a signposting from (e.g. ``"http://example.com/page-01.html"``) (called ``anchor`` in Link header)
        :param link: Optional origin :class:`Link` header (not parsed further) for further attributes

        :raise ValueError: If a plain string value is invalid for the corresponding type-checked classes :class:`LinkRel`, :class:`AbsoluteURI` or :class:`MediaType`,

        """

        if isinstance(rel, LinkRel):
            self.rel = rel
        else:
            self.rel = LinkRel(rel)  # May throw ValueError

        if isinstance(target, AbsoluteURI):
            self.target = target
        else:
            self.target = AbsoluteURI(target)  # may throw ValueError

        if isinstance(media_type, MediaType):
            self.type = media_type
        elif media_type:
            self.type = MediaType(media_type)
        else:
            self.type = None

        if isinstance(profiles, AbstractSet):
            for p in profiles:
                assert isinstance(p, AbsoluteURI)
            self.profiles = frozenset(profiles)
        elif profiles:
            self.profiles = frozenset(AbsoluteURI(p)
                                      for p in profiles.split(" "))
        else:
            self.profiles = frozenset()

        if isinstance(context, AbsoluteURI):
            self.context = context
        elif context:
            self.context = AbsoluteURI(context)  # may throw ValueError

        self.link = link

    def __repr__(self):
        repr = []
        if self.context:
            repr.append("context=%s" % self.context)
        repr.append("rel=%s" % self.rel)
        repr.append("target=%s" % self.target)
        if self.type:
            repr.append("type=%s" % self.type)
        if self.profiles:
            repr.append("profiles=%s" % self.profiles)

        return "<Signpost %s>" % " ".join(repr)

    def __str__(self):
        strs = []
        strs.append("Link: <%s>" % self.target)
        strs.append("rel=%s" % self.rel)
        if self.type:
            strs.append('type="%s"' % self.type)
        if self.profiles:
            strs.append('profile="%s"' % " ".join(self.profiles))
        if self.context:
            strs.append('context="%s"' % self.context)
        return "; ".join(strs)

class Signposting(Iterable[Signpost], Sized):
    """Signposting links for a given resource.

    Links are categorized according to `FAIR`_ `signposting`_ conventions and 
    split into different attributes like `citeAs` or `describedBy`.

    It is possible to iterate over this class or use the `signposts` property to
    find all recognized signposts.

    Note that in the case of a resource not having any signposts, instances
    of this class are considered false.

    .. _signposting: https://signposting.org/conventions/
    .. _FAIR: https://signposting.org/FAIR/
    """

    context_url: Optional[AbsoluteURI]
    """Resource URL this is the signposting for, e.g. a HTML landing page.
    """

    authors: Set[Signpost]
    """Author(s) of the resource (and possibly its items)"""

    describedBy: Set[Signpost]
    """Metadata resources about the resource and its items, typically in a Linked Data format.

    Resources may require content negotiation, check `Signpost.type` attribute
    (if present) for content type, e.g. ``text/turtle``.
    """

    types: Set[Signpost]
    """Semantic types of the resource, e.g. from schema.org"""

    items: Set[Signpost]
    """Items contained by this resource, e.g. downloads.

    The content type of the download may be available as `Signpost.type` attribute.
    """

    linksets: Set[Signpost]
    """Linkset resuorces with further signposting.

    A `linkset`_ is a JSON or text serialization of Link headers available as a
    separate resource, and may be used to externalize large collection of links, e.g.
    thousands of "item" relations.

    Resources may require content negotiation, check ``Link["type"]`` attribute
    (if present)  for content types ``application/linkset`` or ``application/linkset+json``.

    .. _linkset: https://datatracker.ietf.org/doc/draft-ietf-httpapi-linkset/
    """

    citeAs: Optional[Signpost]
    """Persistent Identifier (PID) for this resource, preferred for citation and permalinks"""

    license: Optional[Signpost]
    """Optional license of this resource (and presumably its items)"""

    collection: Optional[Signpost]
    """Optional collection this resource is part of"""

    def __init__(self, context_url: Union[AbsoluteURI, str] = None, signposts: List[Signpost] = None):
        """Construct a Signposting from a list of :class:`Signpost`s.
        The ``context_url` is the resource this is the signposting for.
        """
        if context_url:
            self.context_url = AbsoluteURI(context_url)
        else:
            self.context_url = None

        # Initialize attributes with empty defaults
        self.citeAs = None
        self.license = None
        self.collection = None
        self.authors = set()
        self.describedBy = set()
        self.items = set()
        self.linksets = set()
        self.types = set()
        self._extras = set() # Any extra signposts, ideally none

        if signposts is None:
            return
        # Populate from list of signposts
        for s in signposts:
            # TODO: Replace with match..case requires Python 3.10+ (PEP 634)
            # match s.rel:
            #    case LinkRel.cite_as:
            #        self.citeAs = s
            #    case LinkRel.license:
            # ...
            if s.rel is LinkRel.cite_as:
                if self.citeAs:
                    warnings.warn("Ignoring additional cite-as signposts")
                    self._extras.add(s)
                else:
                    self.citeAs = s
            elif s.rel is LinkRel.license:
                if self.license:
                    warnings.warn("Ignoring additional license signposts")
                    self._extras.add(s)
                else:
                    self.license = s
            elif s.rel is LinkRel.collection:
                if self.collection:
                    warnings.warn("Ignoring additional collection signposts")
                    self._extras.add(s)
                else:
                    self.collection = s
            elif s.rel is LinkRel.author:
                self.authors.add(s)
            elif s.rel is LinkRel.describedby:
                self.describedBy.add(s)
            elif s.rel is LinkRel.item:
                self.items.add(s)
            elif s.rel is LinkRel.linkset:
                self.linksets.add(s)
            elif s.rel is LinkRel.type:
                self.types.add(s)
            else:
                warnings.warn("Unrecognized link relation: %s" % s.rel)
                # NOTE: This means a new enum member in LinkRel that we should handle above
                self._extras.add(s)

    @property
    def signposts(self) -> AbstractSet[Signpost]:
        """Return all FAIR Signposts for recognized relation types.
        
        This may include any additional signposts for link relations
        that only expect a single link, like :prop:`citeAs`.

        It is also possible to iterate directly over this class, see
        :meth:`__iter__`
        """
        return frozenset(self)

    def __len__(self):
        """Count how many FAIR Signposts were recognized"""
        return len(self.signposts)
    
    def __iter__(self) -> Iterator[Signpost]:
        """Iterate over all recognized FAIR signposts.

        See also the property :prop:`signposts`
        """
        if self.citeAs:
            yield self.citeAs
        if self.license:
            yield self.license
        if self.collection:
            yield self.collection
        for a in self.authors:
            yield a
        for d in self.describedBy:
            yield d
        for i in self.items:
            yield i
        for t in self.types:
            yield t
        for e in self._extras:
            yield e

    def _repr_signposts(self, signposts):
        return " ".join(set(d.target for d in signposts))

    def __repr__(self):
        repr = []
        if self.context_url:
            repr.append("context=%s" % self.context_url)
        if self.citeAs:
            repr.append("citeAs=%s" % self.citeAs.target)
        if self.license:
            repr.append("license=%s" % self.license.target)
        if self.collection:
            repr.append("collection=%s" % self.collection.target)
        if self.authors:
            repr.append("authors=%s" % self._repr_signposts(self.authors))
        if self.describedBy:
            repr.append("describedBy=%s" % self._repr_signposts(self.describedBy))
        if self.items:
            repr.append("items=%s" % self._repr_signposts(self.items))
        if self.linksets:
            repr.append("linksets=%s" % self._repr_signposts(self.linksets))
        if self.types:
            repr.append("types=%s" % self._repr_signposts(self.types))

        return "<Signposting %s>" % "\n ".join(repr)

    def __str__(self):
        """Represent signposts as HTTP Link headers.
        
        Note that these are reconstructed from the recognized link relations only,
        and do not include unparsed additional link attributes.

        See also `Signpost.link`
        """
        return "\n".join(map(str, self))

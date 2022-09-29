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

# PEP-563 support self-references of types in class definitions
from __future__ import annotations

import itertools
import re
from typing import Collection, Iterable, Iterator, List, Optional, Set, Sized, Tuple, Union, AbstractSet, FrozenSet
from enum import Enum, auto, unique
from warnings import warn

import rfc3987
import urllib.parse
from urllib.parse import urljoin
from httplink import Link

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

    This is a convenience class that may be wrapping a :attr:`link`
    or otherwise constructed.

    In some case the link relation may have additional attributes,
    e.g. ``signpost.link["title"]`` - the purpose of this class is however to
    lift only the navigational attributes for FAIR Signposting.
    """

    rel: LinkRel
    """The link relation of this signposting"""

    target: AbsoluteURI
    """The URI that is the target of this link, e.g. ``http://example.com/``
    
    Note that URIs with Unicode characters will be represented as %-escaped URIs rather than as IRIs.
    """

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

    There may be multiple profiles, or (more commonly) none.
    """

    context: Optional[AbsoluteURI]
    """Resource URL this is the signposting for, e.g. a HTML landing page.

    Note that following HTTP redirections means this URI may be different
    from the one originally requested.

    This attribute is optional (with ``None`` indicating unknown context),
    however producers of ``Signpost`` instances from are encouraged to 

    """

    link: Optional[Link]
    """The Link object this signpost was created from.

    May contain additional attributes such as ``link["title"]``.
    Note that a single Link may have multiple ``rel``s, therefore it is
    possible that multiple :class:`Signpost` refer to the same link.
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
        else:
            self.context = None

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
            repr.append("profiles=%s" % " ".join(self.profiles))

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
            strs.append('anchor="%s"' % self.context)
        return "; ".join(strs)

    def _eq_attribs(self) -> Iterable[object]:
        """Attributes of the Signpost important for equality testing,
        returned in a predictable (but undefined) order.
        
        This method is used by __eq__ and __hash__ internally.
        
        Subclasses are encouraged to overwrite and add additional attributes
        in a consistent order at the end."""
        # NOTE: context **is** included in equality so that multiple Signpost
        # objects can be in the set of Signposting. For instance, there can be
        # multiple documents that share the same metadata resource.
        yield self.context
        yield self.rel
        yield self.target
        yield self.type
        # NOTE: do NOT yield each profile of set separately, as order is not consistent
        # As self.profiles is a frozenset it is elligble for hash()
        yield self.profiles

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Signpost):
            return False
        # Assume _eq_attribs has consistent ordering.
        for a,b in zip(self._eq_attribs(), o._eq_attribs()):
            if a != b:
                return False
        return True
    
    def __hash__(self) -> int:
        h = hash(self.__class__.__qualname__)
        for e in self._eq_attribs():
            # Classic XOR would mean order does not matter, but
            # links may have URIs swapped around. As that is unlikely
            # for real-life signposts, we don't need to include 
            # a positional hashing like in hash(tuple)
            h ^= hash(e)
        return h

    def with_context(self, context: Union[AbsoluteURI, str, None]) -> Signpost:
        """Create a copy of this signpost, but with the specified context.
        
        If the context is None, it means the copy will not have a context.
        """
        return Signpost(self.rel, self.target, self.type, self.profiles, context, self.link)

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
    """Resource URI this is the signposting for, e.g. a HTML landing page, hereafter called "this resource".
    
    This attribute is optional, `None` indicate
    no context filtering applies and that
    individual signposts can have any context.
    """

    other_contexts: Set[AbsoluteURI]
    """Other resource URLs which signposting has been provided for. 
    
    Use :meth:`for_context` to retrieve their signpostings, or filter the full list of signposts from :attr:`signposts` according to :attr:`Signpost.context`
    """

    authors: Set[Signpost]
    """Author(s) of this resource (and possibly its items)"""

    describedBy: Set[Signpost]
    """Metadata resources about this resource and its items, typically in a Linked Data format.

    Resources may require content negotiation, check `Signpost.type` attribute
    (if present) for content type, e.g. ``text/turtle``.
    """

    types: Set[Signpost]
    """Semantic types of this resource, e.g. from schema.org"""

    items: Set[Signpost]
    """Items contained by this resource, e.g. downloads.

    The content type of the download may be available as `Signpost.type` attribute.
    """

    linksets: Set[Signpost]
    """Linkset resources with further signposting for this resource (and potentially others).

    A `Linkset`_ is a JSON or text serialization of Link headers available as a
    separate resource, and may be used to externalize large collection of links, e.g.
    thousands of "item" relations.

    Resources may require content negotiation, check ``Link["type"]`` attribute
    (if present)  for content types ``application/linkset`` or ``application/linkset+json``.

    .. _Linkset: https://datatracker.ietf.org/doc/draft-ietf-httpapi-linkset/
    """

    citeAs: Optional[Signpost]
    """Persistent Identifier (PID) for this resource, preferred for citation and permalinks"""

    license: Optional[Signpost]
    """Optional license of this resource (and presumably its items)"""

    collection: Optional[Signpost]
    """Optional collection resource that the selected resource is part of"""
    
    def __init__(self, 
                 context_url: Union[AbsoluteURI, str] = None, 
                 signposts: Iterable[Signpost] = None,
                 include_no_context: bool = True,
                 warn_duplicate=True):
        """Construct a Signposting from a list of :class:`Signpost`s.

        Signposts are filtered by the matching `context_url` (if provided), 
        then assigned to attributes like :attr:`citeAs` or :attr:`describedBy`
        depending on their :attr:`Signpost.rel` link relation.

        Multiple signposts discovered for singular relations like ``citeAs`` 
        are ignored in this attribute assignment, however these are included in
        the `Iterable` interface of this class and thus also in its length.

        A Signposting object is equivalent to boolean `False` in conditional expression 
        if it is empty, that is ``len(signposting)==0``, indicating no signposts 
        were discovered for the given context. However the remaining 
        ``signposts`` will still be available from :attr:`signposts`, as
        indicated by :attr:`other_contexts`.
        
        :param context_url: the resource to select signposting for, or any signposts if ``None``.            
        :param signposts: An iterable of :class:`Signpost`s that should be considered for selecting signposting.
        :param include_no_context: If true (default), consider signposts without explicit context, 
            assuming they are about ``context_url``. 
            If false, such signposts are ignored for assignment, 
            but remain available from :attr:`signposts`.
        :param warn_duplicate: If true (default), warn of duplicate signposts that can't be assigned.
        :raise ValueError: If ``include_no_context`` is false, but ``context_url`` was not provided or None.
        """
        if not include_no_context and not context_url:
            raise ValueError("Can't exclude signposts without context when not providing context_url; try include_no_context=True")

        if context_url:
            self.context_url = AbsoluteURI(context_url)
        else:
            self.context_url = None # No filtering

        # Initialize attributes with empty defaults
        self.citeAs = None
        self.license = None
        self.collection = None
        self.authors = set()
        self.describedBy = set()
        self.items = set()
        self.linksets = set()
        self.types = set()
        self.other_contexts = set()
        self._extras = set() # Any extra signposts, ideally empty
        self._others = set() # Signposts with a different context

        if signposts is None:
            return # We're empty
        # Populate above attributes from list of signposts
        for s in signposts:
            if include_no_context and not s.context:
                # Pretend it's in our context
                context = self.context_url
            else:
                # Inspect signposts's context
                context = s.context

            if self.context_url and self.context_url != context:
                self._others.add(s)
                if context:
                    self.other_contexts.add(context)
            elif s.rel is LinkRel.cite_as:
                if self.citeAs and self.citeAs.target != s.target:
                    warn("Ignoring additional cite-as signposts") if warn_duplicate else None
                    self._extras.add(s)
                else:
                    self.citeAs = s
            elif s.rel is LinkRel.license:
                if self.license and self.license.target != s.target:
                    warn("Ignoring additional license signposts") if warn_duplicate else None
                    self._extras.add(s)
                else:
                    self.license = s
            elif s.rel is LinkRel.collection:
                if self.collection and self.collection.target != s.target:
                    warn("Ignoring additional collection signposts") if warn_duplicate else None
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
                warn("Unrecognized link relation: %s" % s.rel)
                # NOTE: This means a new enum member in LinkRel that we should handle above
                self._extras.add(s)

    @property
    def signposts(self) -> AbstractSet[Signpost]:
        """All FAIR Signposts with recognized relation types.
        
        This may include any additional signposts for link relations
        that only expect a single link, like :prop:`citeAs`, as well
        as any signposts for other contexts as listed in :prop:`other_contexts`.
        """
        return frozenset(itertools.chain(self, self._others))

    def _signposts_with_explicit_context(self) -> Iterable[Signpost]:
        """Iterate over all our signposts, making context explicit if possible.

        Variant of ::attr:signposts, gives a generator.

        If ::attr:`context_url` is set, then signposts without a context will be
        excluded (to avoid them leaking across contexts). 
        """
        for s in self:
            if not s.context and self.context_url:
                # Clone to make implicit context explicit
                yield s.with_context(self.context_url)
            else:
                yield s
        for o in self._others:
            if not o.context and self.context_url: 
                warn("Ignoring signpost with unknown context: %s" % o)
                continue
            yield o

    def for_context(self, context_uri:Union[AbsoluteURI, str, None]) -> Signposting:
        """Return signposting for given context URI.
        
        This will select an alternative view of the signposts from :attr:`signposts`
        filtered by the given ``context_uri``.

        The remaining signposts and their contexts will be included under 
        :attr:`Signpost.signposts` -- any signposts with implicit context will
        be replaced with having an explicit context :attr:`self.context_url`.

        **Tip**: To ensure all signposts have explicit context, use 
        ``s.for_context(s.context_uri)``

        :param context_uri: The context to select signposts from. 
            The URI should be a member of :attr:`contexts` or equal to :attr:`context`, 
            otherwise the returned Signposting will be empty.
            If the context_uri is `None`, then the :attr:`Signpost.context` is ignored
            and any signposts will be considered.
        """
        include_no_context = context_uri is None
        if include_no_context:
            # include any implicit contexts as-is
            our_signposts: Iterable[Signpost] = self.signposts
        else:
            # ensure explicit contexts, so they don't get lost
            our_signposts = self._signposts_with_explicit_context()
        return Signposting(context_uri, 
                           our_signposts,
                           include_no_context=include_no_context)

    def __len__(self) -> int:
        """Count how many FAIR Signposts were recognized for the given context"""
        # Note: tuple(self) fails here, as tuple will call our __len__ to pre-allocate
        #return len(tuple(self))
        # Instead we'll do it with a nice generator
        return sum(1 for _ in self)
    
    def __iter__(self) -> Iterator[Signpost]:
        """Iterate over all FAIR signposts recognized for the given context.

        See also the property :prop:`signposts` for signposts of any context.
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
        # NOTE: self._others are NOT included as they have a different context

    def __eq__(self, o) -> bool:
        """A Signposting instance is equal to another Signposting, 
        if and only if it has the same `Signpost`s for their respective
        current contexts.
        
        Note that their :attr:`Signposting.context_url` are _not_ compared for equality,
        although each :attr:`Signpost.context` are included when comparing list of signposts. 
        This distinction becomes significant when comparing signposts without explicit
        context, loaded from two different contexts.

        **Tip**: To compare two Signposting's using only explicit ``Signpost.context``s, use
        ``a.for_context(a.context_uri) == b.for_context(b.context_uri)``
        """
        if not isinstance(o, Signposting):
            return False
        return set(self) == set(o)

    def __hash__(self) -> int:
        """Calculate a hash of this Signposting instance based on its equality.
        
        The result of this hash method is consistent with :meth:`__eq__` in that
        only each signpost of the current context are part of the calculation.
        """
        h = hash(self.__class__.__qualname__)
        # NOTE context is NOT included in equality checks, see __eq__
        ## h ^= self.context_url
        for e in self:
            # We use a naive XOR here as order should NOT matter
            h ^= hash(e)
        # Signposts in other contexts are ignored
        ##for e in self._others:
        ##    h ^= hash(e)
        return h

    def _repr_signposts(self, signposts) -> str:
        """String representation of a list of signposts"""
        # This is usually a short list, so no need for max-trimming and ...
        return " ".join(set(d.target for d in signposts))

    def __repr__(self) -> str:
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
        if self.other_contexts:
            repr.append("other_contexts=%s" % " ".join(self.other_contexts))

        return "<Signposting %s>" % "\n ".join(repr)

    def __str__(self) -> str:
        """Represent all :atttr:`signposts` as HTTP Link headers.
        
        Note that these are reconstructed from the recognized link relations only,
        and do not include unparsed additional link attributes.
        
        Signposts with other contexts are included in this listing.

        See also `Signpost.link`
        """
        return "\n".join(map(str, self.signposts))

    def __or__(self, other: Signposting) -> Signposting:
        """Merge two Signposting instances.
        
        The context of the new Signposting is determined as:  
        
        a) The context of the left-hand Signposting, if explicit; or
        b) The context of the right-hand Signposting, if explicit; or
        c) No context
        
        When merging Signpost, any implicit contexts are made explicit
        from their original :attr:`Signposting.context_url` if specified. 
        
        If neither Signposting has a context, then the new `Signposting`
        is constructed with ``include_no_context=True`` meaning that only
        signposts _without_ context are considered. Otherwise only
        signpost _with_ the determined context are considered. 
        
        **Tip**: To adapt signposts without context, use :meth:`Signposting.__add__` instead

        If multiple signposts match singular properties like :attr:`citeAs` but with 
        different targets, Signpost from this instance (left-hand) 
        will be preferred after merging, however all signposts will be 
        included in the iteration over the returned ``Signposting``. 

        Duplicate Signpost (as determined by :meth:`Signpost.__eq__`) 
        will be ignored, it is unspecified which Signpost will be rejected 
        (this should primarily affects :attr:`Signpost.link`).

        As an example, if the left-hand Signpost ``a`` with context ``http://example.com/doc/1`` had::

            Link <http://example.com/pid/A>;rel=cite-as
            Link <http://example.com/author/1>;rel=author``
            
        and the right-hand ``b`` with context ``http://example.com/doc/2`` had::

            Link <http://example.com/pid/B>;rel=cite-as"
            Link <http://example.com/author/2>;rel=author;context="http://example.com/doc/1`

        then the resulting Signposting ``a|b`` would contain::

            Link <http://example.com/pid/A;rel=cite-as;context="http://example.com/doc/1"
            Link <http://example.com/author/1>;rel=author;context="http://example.com/doc/1"
            Link <http://example.com/author/2>;rel=author;context="http://example.com/doc/1"

        In this case ``…pid/B`` is ignored in the merged signposting as it relates to ``…doc/2`` 
        and not the determined context ``http://example.com/doc/1``, which on the other hand
        has been made explicit in all its direct signposts.

        The complete set of merged signposts (regardless of their context) 
        is available in :attr:`Signposting.signposts` in the returned instance.

        :param other: Another `Signposting` instance which signposts are to be merged with ours
        :return: A new `Signposting` instance from the merged list of signposts. 
        :raise TypeError: If `other` is not an instance of `Signposting`
        """
        if not isinstance(other, Signposting):
            raise TypeError("Can only merge with Signposting instances, not: " % type(other))
        # Decide if the merged Signposting will have a context. 
        # Left hand has preference.
        newContext = self.context_url or other.context_url or None
        if newContext:
            # Merge with explicit contexts so that Signposts can be compared
            merged: Iterable[Signpost] = itertools.chain(self._signposts_with_explicit_context(), 
                    other._signposts_with_explicit_context())
        else:
            # Both are context-free, merge them as-is, but prefer self
            merged = itertools.chain(self.signposts,other.signposts)
        return Signposting(newContext, merged,                            
                           include_no_context=not newContext,
                           warn_duplicate=False)

    def __add__(self, other: Union[Signposting, Iterable[Signpost]]) -> Signposting:
        """Create a merged Signposting by overriding new Signposts from another.

        The returned Signposting instance will have the same context as this instance.

        `other` is considered an iterable of `Signpost`s -- if it is a `Signposting` instance,
        this method will iterate over its direct signposts only if its context is ``None`` or matches
        the current context, otherwise it will select the current context using :meth:`Signposting.for_context`.
        
        If the added Signpost's context is `None` or match the current :attr:`context_uri`` 
        they will __replace__ or append the existing signposts from this instance. 
        
        For instance, if the left-hand Signpost ``a`` had::

            Link <http://example.com/pid/A>;rel=cite-as
            Link <http://example.com/author/1>;rel=author``
            
        and the right-hand ``b`` had::

            Link <http://example.com/pid/B>;rel=cite-as
            Link <http://example.com/author/2>;rel=author

        then the resulting Signposting ``a+b`` would contain::

            Link <http://example.com/pid/B>;rel=cite-as
            Link <http://example.com/author/1>;rel=author``
            Link <http://example.com/author/2>;rel=author

        (Note: iterating over the returned `Signposting` would include the relegated ``…pid/A``. 
        Take care of operatand order if adding multiple Signpostings).
        
        Added signposts with other contexts will be ignored and
        __not__ added to the resulting `signposts`, however existing 
        signposts from other contexts in this instance are preserved.

        To do a full merge across contexts, use instead ``a | b``, see :meth:`__or__`

        :param other: Either an `Iterable` (`Set`, `List`, etc) of `Signpost` instances, or another `Signposting` instance.
            The signposts are to be added to our signposts, if matching the determined context.
        :return: A new `Signposting` instance from the summed list of signposts. 
            Signposts from `other` may overridde signposts from this instance.
        :raise TypeError: If `other` is not an instance of `Signposting` or an iterable of Signposts.
        """
        if (isinstance(other, Signposting) and 
                self.context_url and other.context_url and 
                other.context_url != self.context_url):
            to_add: Iterable[Signpost] = other.for_context(self.context_url)
        else:
            to_add = (s for s in other if s.context == self.context_url or not s.context)
        return Signposting(self.context_url, itertools.chain(to_add, self.signposts), 
            # NOTE: We chain the added ones first so they can override the singular properties like citeAs
                include_no_context=True, warn_duplicate=False)

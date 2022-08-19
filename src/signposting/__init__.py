"""Finding signposting in FAIR resources.

This library helps client to discover links that follow the
`FAIR`_ `signposting`_ conventions.

This can then be used to navigate between:

* Persistent identifiers
* HTML landing pages
* File downloads/items
* Structured metadata

The library works by inspecting the HTTP messages for
``Link:`` headers from a given URI with :meth:`find_signposting_http`, which
which categorize them by their ``rel`` `Link relation`_ into a
:class:`Signposting` object with absolute URIs.

It is up to the clients of this library to decide how to further
navigate or retrieve the associated resources, e.g. using a
RDF library like :mod:`rdflib`.

This library also provide ways to discover
FAIR signposting in HTML ``<link>`` annotations and in
`linkset`_ documents.  Future versions may provide ways to 
discover/merge these concurently.

.. _signposting: https://signposting.org/conventions/
.. _FAIR: https://signposting.org/FAIR/
.. _Link Relation: https://www.iana.org/assignments/link-relations/
.. _rdflib: https://rdflib.readthedocs.io/en/stable/
.. _linkset: https://signposting.org/FAIR/#linksetrec
"""

__version__ = '0.6.1'

from typing import List
import warnings
from .signpost import Signposting, Signpost, AbsoluteURI, MediaType, LinkRel
from .linkheader import find_signposting_http_link
from .resolver import find_signposting_http
from .htmllinks import find_signposting_html
from .linkset import find_signposting_linkset

def find_signposting(headers: List[str], baseurl: str = None) -> Signposting:
    """DEPRECATED: Use meth:`find_signposting_http_link` instead"""
    warnings.warn("find_signposting() is deprecated, use find_signposting_http_link()")
    return find_signposting_http_link(headers, baseurl)

__all__ = """find_signposting_http_link find_signposting_http find_signposting_html find_signposting_linkset
Signposting Signpost AbsoluteURI MediaType LinkRel""".split()

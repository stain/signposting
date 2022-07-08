"""Finding signposting in FAIR resources.

This library helps client to discover links that follow the 
`FAIR`_ `signposting`_ conventions.

This can then be used to navigate between:

* Persistent identifiers
* HTML landing pages
* File downloads/items
* Structured metadata

The library works by inspecting the HTTP messages for
``Link:`` headers from a given URI with `find_signposting_http`, which
which categorize them by their `rel` `Link relation`_ into a 
`Signposting` object with absolute URIs.

It is up to the clients of this library to decide how to further
navigate or retrieve the associated resources, e.g. using a 
RDF library like `rdflib`_.

Future versions of this library may also provide ways to discover
FAIR signposting in HTML ``<link>`` annotations and in 
`linkset`_ documents.

.. _signposting: https://signposting.org/conventions/
.. _FAIR: https://signposting.org/FAIR/
.. _Link Relation: https://www.iana.org/assignments/link-relations/
.. _rdflib: https://rdflib.readthedocs.io/en/stable/
.. _linkset: https://signposting.org/FAIR/#linksetrec
"""

__version__ = '0.2.3'

from .linkheader import Signposting, find_signposting
from .resolver import find_signposting_http
from .signpost import Signposting, Signpost, AbsoluteURI, MediaType, LinkRel

__all__ = """Signposting find_signposting find_signposting_http
Signposting Signpost AbsoluteURI MediaType LinkRel""".split()

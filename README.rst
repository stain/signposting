===============================
Signposting link parser library
===============================
*Finding signposting in FAIR resources*

.. image:: https://img.shields.io/pypi/v/signposting
    :target: https://pypi.org/project/signposting/
    :alt: pypi install signposting

.. image:: https://img.shields.io/pypi/pyversions/signposting
    :target: https://pypi.org/project/signposting/
    :alt: Python

.. image:: https://img.shields.io/github/license/stain/signposting
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Apache License v.2.0

.. image:: https://github.com/stain/signposting/workflows/Tests/badge.svg?branch=main
    :target: https://github.com/stain/signposting/actions?workflow=Tests
    :alt: Test Status

.. image:: https://github.com/stain/signposting/workflows/Package%20Build/badge.svg?branch=main
    :target: https://github.com/stain/signposting/actions?workflow=Package%20Build
    :alt: Package Build

.. image:: https://codecov.io/gh/stain/signposting/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/stain/signposting
    :alt: Codecov

.. image:: https://img.shields.io/readthedocs/signposting/latest?label=Read%20the%20Docs
    :target: https://signposting.readthedocs.io/en/latest/index.html
    :alt: Read the Docs

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.6815412.svg
   :target: https://doi.org/10.5281/zenodo.6815412
   :alt: DOI 10.5281/zenodo.6815412



Summary
=======
This library helps client to discover links that follow the 
`signposting`_ conventions, most notably `FAIR Signposting`_.

This can then be used to navigate between:

* Persistent identifiers
* HTML landing pages
* File downloads/items
* Structured metadata

Method
=======

The library works by inspecting the HTTP messages for
``Link`` headers from a given URI with `find_signposting_http`, which
which categorize them by their `rel` `Link relation`_ into a 
`Signposting` object with absolute URIs.

It is up to the clients of this library to decide how to further
navigate or retrieve the associated resources, e.g. using a 
RDF library like `rdflib`_ or retrieving resources using `urllib`_.

Future versions of this library may also provide ways to discover
FAIR signposting in HTML ``<link>`` annotations and in 
`linkset`_ documents.


Motivation
==========

`FAIR Signposting`_ has been proposed as a mechanism for automated clients to find 
metadata and persistent identifiers for FAIR data residing in repositories that follow
the traditional PID-to-landing-page metaphor. 

This avoids the need for client guesswork with content-negotiation, and allows structured 
metadata to be provided by the repository rather than just PID providers like DataCite. 

The main idea of FAIR Signposting is to re-use the existing HTTP mechanism for links, using
existing relations like ``describedby``, ``cite-as`` and ``item``.

The aim of this library is to assist such clients to find and consume FAIR resources
for further processing. It is out of scope for this code to handle parsing of the 
structured metadata files.


Acknowledgments
===============

Contributors:

* Stian Soiland-Reyes <https://orcid.org/0000-0001-9842-9718>

Acknowledgements to Mark Wilkinson, Herbert van de Sompel, Finn Bacall.


How to use this repository
==========================

The `documentation`_ pages explain briefly how to use this library including a listing of modules and methods.


Issues and Discussions
======================

As usual in any GitHub based project, raise an `issue`_ if you find any bug or have other suggestions; or open a `discussion`_  if you want to discuss or talk :-)

Version
=======

v0.8.1

.. _GitHub Actions: https://github.com/features/actions
.. _PyPI: https://pypi.org
.. _bump2version: https://github.com/c4urself/bump2version
.. _discussion: https://github.com/stain/signposting/discussions
.. _documentation: https://signposting.readthedocs.io/
.. _issue: https://github.com/stain/signposting/issues
.. _main branch: https://github.com/stain/signposting/tree/main
.. _pdb-tools: https://github.com/haddocking/pdb-tools
.. _project's documentation: https://signposting.readthedocs.io/en/latest/index.html
.. _pytest: https://docs.pytest.org/en/stable/git
.. _test.pypi.org: https://test.pypi.org
.. _ReadTheDocs: https://readthedocs.org/
.. _signposting: https://signposting.org/conventions/
.. _FAIR Signposting: https://signposting.org/FAIR/
.. _Link Relation: https://www.iana.org/assignments/link-relations/
.. _rdflib: https://rdflib.readthedocs.io/en/stable/
.. _urllib: https://docs.python.org/3/library/urllib.html
.. _linkset: https://signposting.org/FAIR/#linksetrec


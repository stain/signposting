
Changelog
=========

* Signpost objects support for ``==`` and ``hash()``

v0.7.1 (2022-08-22)
------------------------------------------------------------

v0.7.0 (2022-08-20)
------------------------------------------------------------

* Support multiple context in ``Signposting`` -- users of ``find_signposting_linkset`` should take particularly care to look up using ``for_context``
* RFC7231 update: Don't resolve context according to ``Content-Location`` header

v0.6.1 (2022-08-19)
------------------------------------------------------------

* `find_signposting_linkset` listed in module

v0.6.0 (2022-08-14)
------------------------------------------------------------

* Linkset parsing exposed as ``find_signposting_linkset``
* Optional explicit content-negotiate for linksets
* Integration tests for linksets using a2a-fair-metrics benchmarks

v0.5.2 (2022-08-14)
------------------------------------------------------------

* Handle missing Content-Type header

v0.5.1 (2022-08-14)
------------------------------------------------------------

* Unit tests compatible with Python 3.7

v0.5.0 (2022-08-13)
------------------------------------------------------------

* Add experimental RFC9264 linkset parsing (text and json)

v0.4.0 (2022-08-13)
------------------------------------------------------------

* Renamed deprecated ``find_signposting``, renamed to ``find_signposting_http_link``
* More unit tests for ``signposting.htmllinks``

v0.3.3 (2022-08-12)
------------------------------------------------------------

* Documentation update

v0.3.2 (2022-08-12)
------------------------------------------------------------

* Unit tests for ``signposting.htmllinks``

v0.3.1 (2022-08-11)
------------------------------------------------------------

* Refactor ``signposting.htmllinks`` module

v0.3.0 (2022-08-09)
------------------------------------------------------------

* Expose ``find_signposting_html`` in public API

v0.2.6 (2022-08-09)
------------------------------------------------------------

* Improved type safety in ``htmllinks``


v0.2.5 (2022-08-08)
------------------------------------------------------------

* Further documentation improvements
* Initial HTML parsing of <link> elements (import ``signposting.htmllinks`` for now)
* Added str/repr for ``Signposting`` and ``Signpost`` classes. ``str(s)`` return HTTP link headers.
* Added ``Signposting.signposts`` property
* ``Signposting`` is now iterable

v0.2.4 (2022-07-08)
------------------------------------------------------------

* Documentation improvements

v0.2.3 (2022-07-08)
------------------------------------------------------------

* Documentation update

v0.2.2 (2022-06-07)
------------------------------------------------------------

* Tidy up ``__init__.py`` public API

v0.2.1 (2022-06-05)
------------------------------------------------------------

* API Change: Refactored to new ``Signposting`` classes
  to avoid exposing the ``ParsedLink`` implementation.
* Note: ``Signposting`` attributes like ``.authors`` are now
  sets to indicate order is not (very) important.
* Removed rdflib dependency

v0.1.3 (2022-05-17)
------------------------------------------------------------
* Hide for now draft implementation

v0.1.2 (2022-05-17)
------------------------------------------------------------
* Draft implementation of ``Signposting`` classes

v0.1.1 (2022-04-13)
------------------------------------------------------------

* Build improvements

v0.1.0 (2022-04-13)
------------------------------------------------------------

* First 0.1 release

v0.0.15 (2022-04-13)
------------------------------------------------------------
* Documentation improvements

v0.0.14 (2022-04-13)
------------------------------------------------------------
* Documentation improvements

v0.0.13 (2022-04-13)
------------------------------------------------------------
* Documentation improvements

v0.0.12 (2022-04-13)
------------------------------------------------------------
* Documented example

v0.0.11 (2022-04-13)
------------------------------------------------------------
* Fix integration test for PID typo <https://w3id.org/a2a-fair-metrics/11-http-describedby-iri-wrong-type/>

v0.0.10 (2022-04-12)
------------------------------------------------------------
* Fix integration tests for PID typos <https://w3id.org/a2a-fair-metrics/24-http-citeas-204-no-content/> <https://w3id.org/a2a-fair-metrics/25-http-citeas-author-410-gone/> <https://w3id.org/a2a-fair-metrics/26-http-citeas-203-non-authorative/>
* Added rudimentary tests for <https://w3id.org/a2a-fair-metrics/27-http-linkset-json-only/> and <https://w3id.org/a2a-fair-metrics/28-http-linkset-txt-only/>
* Added tests for <https://w3id.org/a2a-fair-metrics/30-http-citeas-describedby-item-license-type-author-joint/>

v0.0.9 (2022-04-11)
------------------------------------------------------------
* Documented changelog for old versions

v0.0.8 (2022-04-11)
------------------------------------------------------------
 * Command line tool tested

v0.0.7 (2022-04-11)
------------------------------------------------------------
* Command line tool functional

v0.0.6 (2022-04-11)
------------------------------------------------------------
* Initial draft of command line tool

v0.0.5 (2022-04-10)
------------------------------------------------------------
* Handle 410 Gone and 203 Non-Authorative as warnings
* Tests against HTTP aspects of <https://s11.no/2022/a2a-fair-metrics/> for #1--#26

v0.0.4 (2022-04-06)
------------------------------------------------------------
* API Documentation drafted
* `find_landing_page` renamed `find_signposting_http`

v0.0.3 (2022-04-06)
------------------------------------------------------------
* README updates
* More tests until a2a-fair-metrics test #17

v0.0.2 (2022-04-06)
------------------------------------------------------------
* Initial HTTP Link header parsing

v0.0.1 (2022-04-01)
------------------------------------------------------------
* Generated from joaomcteixeira/python-project-skeleton


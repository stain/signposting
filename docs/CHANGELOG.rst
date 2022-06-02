
Changelog
=========

* API Change: Refactored to new ``Signposting`` classes
  to avoid exposing the ``ParsedLink`` implementation.
* Note: ``Signposting`` attributes like ``.authors`` are now
  sets to indicate order is not (very) important.
* Removed rdflib dependency

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


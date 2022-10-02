=====
Usage
=====

To use ``signposting`` from Python::

	import signposting
	s = signposting.find_signposting_http(
		"https://w3id.org/a2a-fair-metrics/05-http-describedby-citeas/")
	print(s.citeAs)
	print(s.citeAs.target)
	for d in s.describedBy:
		print(d.target)
		print(d.type)

The :class:`signposting.Signposting` object returned points to
:class:`signposting.Link` instances which have attributes matching the FAIR
signposting profile.

If no signposting was found for a link relation, its attributes return ``None`` or an empty list depending on its cardinality.

A convenience command line tool ``signposting`` will be installed::

	$ signposting https://w3id.org/a2a-fair-metrics/05-http-describedby-citeas
	
	Signposting for https://s11.no/2022/a2a-fair-metrics/05-http-describedby-citeas/
	CiteAs: <https://w3id.org/a2a-fair-metrics/05-http-describedby-citeas/>
	DescribedBy: <https://s11.no/2022/a2a-fair-metrics/05-http-describedby-citeas/index.ttl> text/turtle

A benchmark set of signposted resources (`a2a-fair-metrics`_) is provided for testing purposes. Note that the library currently only 
support the ``"-http-"`` tests.

.. _a2a-fair-metrics: https://w3id.org/a2a-fair-metrics/
.. _Signposting: reference/signposting.html#signposting.Signposting
.. _Link: reference/signposting.html#signposting.Link

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2022 The University of Manchester, UK
#
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
"""Test Signpost classes"""

import itertools
from multiprocessing.sharedctypes import Value
import unittest
import warnings
import uuid

from httplink import Link
from enum import Enum

import signposting.signpost
from signposting.signpost import Signpost, AbsoluteURI, MediaType, LinkRel, Signposting, SIGNPOSTING


class TestAbsoluteURI(unittest.TestCase):
    def testConstructorAbsolute(self):
        self.assertEqual("http://example.com/a.txt",
            AbsoluteURI("http://example.com/a.txt"))

    def testConstructorSelf(self):
        a = AbsoluteURI("http://example.com/")
        b = AbsoluteURI(a) # It's a str, but should not re-wrap
        self.assertEqual(a, b)
        self.assertIs(a, b)

    def testConstructorRelative(self):
        self.assertEqual("http://example.com/foo/a.txt",
            AbsoluteURI("a.txt", "http://example.com/foo/"))

    def testConstructorBaseIgnored(self):
        self.assertEqual("http://example.com/a.txt",
            AbsoluteURI("http://example.com/a.txt", "http://other.example.org/"))

    def testConstructorRelativeWithoutBaseFails(self):
        with self.assertRaises(ValueError):
            AbsoluteURI("a.txt")
        with self.assertRaises(ValueError):
            AbsoluteURI("a.txt", "not/absolute/either")

    def testStr(self):
        # Still stringable
        self.assertEqual("http://example.com/",
                         str(AbsoluteURI("http://example.com/")))
        # Regular string methods still there
        self.assertTrue(AbsoluteURI("http://example.com/").startswith("http://"))

    def testEquals(self):
        self.assertEqual("http://example.com/",
                         AbsoluteURI("http://example.com/"))
        self.assertEqual(AbsoluteURI("http://example.com/"),
                         "http://example.com/")

    def testNotAbsolute(self):
        with self.assertRaises(ValueError):
            AbsoluteURI("/relative/path.html")

    def testNotValidURL(self):
        with self.assertRaises(ValueError):
            AbsoluteURI("http: // not valid")


class TestLinkRel(unittest.TestCase):
    def testEqual(self):
        self.assertEqual("cite-as", LinkRel.cite_as)
        self.assertEqual(LinkRel.cite_as, "cite-as")

    def testStrMethods(self):
        self.assertTrue(LinkRel.cite_as.startswith("cite"))
        self.assertTrue(LinkRel.cite_as.endswith("-as"))

    def testStr(self):
        self.assertEqual("author",
                         str(LinkRel.author))
        self.assertEqual("collection",
                         str(LinkRel.collection))
        self.assertEqual("describedby",
                         str(LinkRel.describedby))
        self.assertEqual("item",
                         str(LinkRel.item))
        self.assertEqual("cite-as",
                         str(LinkRel.cite_as))
        self.assertEqual("type",
                         str(LinkRel.type))
        self.assertEqual("license",
                         str(LinkRel.license))
        self.assertEqual("linkset",
                         str(LinkRel.linkset))

    def testRepr(self):
        self.assertEqual("rel=cite-as", repr(LinkRel.cite_as))

    def testGetItem(self):
        self.assertEqual(LinkRel.type, LinkRel("type"))
        self.assertEqual(LinkRel.cite_as, LinkRel("cite-as"))
        with self.assertRaises(ValueError):
            LinkRel("stylesheet")  # Registered relation, but not signposting

    def testSIGNPOSTING(self):
        for l in SIGNPOSTING:
            self.assertEqual(l, LinkRel(l).value)
        for l in LinkRel:
            self.assertTrue(l.value in SIGNPOSTING)

class TestMediaType(unittest.TestCase):
    def testTextPlain(self):
        self.assertEqual("text/plain",
                         MediaType("text/plain"))

    def testCaseInsensitive(self):
        self.assertEqual("text/plain",
                         MediaType("Text/PLAIN"))

    def testValidMains(self):
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual("application/pdf",
                             MediaType("application/pdf"))
            # A particularly long one with mixedCasing
            self.assertEqual("application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml".lower(),
                             MediaType("application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml"))
            self.assertEqual("audio/mpeg",
                             MediaType("audio/mpeg"))
            self.assertEqual("example/test",
                             MediaType("example/test"))
            self.assertEqual("font/woff",
                             MediaType("font/woff"))
            self.assertEqual("image/jpeg",
                             MediaType("image/jpeg"))
            self.assertEqual("message/sip",
                             MediaType("message/sip"))
            self.assertEqual("model/vrml",
                             MediaType("model/vrml"))

            self.assertEqual("multipart/mixed",
                             MediaType("multipart/mixed"))
            self.assertEqual("text/html",
                             MediaType("text/html"))
            self.assertEqual("video/mp4",
                             MediaType("video/mp4"))
            self.assertEqual([], w)

    def testOtherTrees(self):
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual("application/ld+json",
                             MediaType("application/ld+json"))
            self.assertEqual("example/vnd.example.test",
                             MediaType("example/vnd.example.test"))
            self.assertEqual("example/prv.example.test",
                             MediaType("example/prv.example.test"))
            self.assertEqual("example/x.example.test",
                             MediaType("example/x.example.test"))
            self.assertEqual([], w)

    def testUnknownTrees(self):
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual("other/example",
                             MediaType("other/example"))
            self.assertEqual(1, len(w))
            self.assertTrue(issubclass(w[0].category, UserWarning))

    def testSurprisinglyValid(self):
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual("example/92-#-z-$-x-&-^-_-+-.",
                             MediaType("example/92-#-z-$-x-&-^-_-+-."))
            self.assertEqual("92-#-z-$-x-&-^-_-/example",  # No +. this time
                             MediaType("92-#-z-$-x-&-^-_-/example"))
            self.assertEqual("9/2",
                             MediaType("9/2"))
        self.assertEqual(2, len(w))  # 92... and 9 invalid main types

    def testInvalidMain(self):
        with warnings.catch_warnings(record=True) as w:
            with self.assertRaises(ValueError):
                MediaType(".example/wrong")  # first character not a-z0-9
            with self.assertRaises(ValueError):
                MediaType("fantasy%text/handwritten")  # % not permitted
            with self.assertRaises(ValueError):
                MediaType(" text/plain")  # Space not permitted
            with self.assertRaises(ValueError):
                MediaType("*/*")  # * not permitted (but common in HTTP Accept!)
            with self.assertRaises(ValueError):
                MediaType("image/*")  # As above, but in sub-type
            with self.assertRaises(ValueError):
                MediaType("-test/example")  # First character not a-z0-9
            with self.assertRaises(ValueError):
                MediaType("example/-test")  # First character not a-z0-9
        self.assertEqual([], w)  # Should fail before testing main type

    def testInvalidLength(self):
        x256 = "x" * 256
        x127 = "x" * 127
        with warnings.catch_warnings(record=True) as w:
            # Maximum on either side
            MediaType("example/" + x127)
            MediaType(x127 + "/example")
            # This is the maximum permissible
            MediaType(x127 + "/" + x127)

            # Total length is over - should ideally
            # fail before running expensive regex
            with self.assertRaises(ValueError):
                MediaType("example/" + x256)
            with self.assertRaises(ValueError):
                MediaType(x256 + "/example")

            # Just over limit on one side only
            with self.assertRaises(ValueError):
                MediaType("example/x" + x127)
            with self.assertRaises(ValueError):
                MediaType(x127 + "x/example")
        # x127 main type unrecognized (second time filtered)
        self.assertEqual(1, len(w))

    def testInvalidType(self):
        with self.assertRaises(ValueError):
            MediaType("text/plain/vanilla")
        with self.assertRaises(ValueError):
            MediaType("text")
        with self.assertRaises(ValueError):
            MediaType("application/")
        with self.assertRaises(ValueError):
            MediaType("application/with space")
        with self.assertRaises(ValueError):
            MediaType("application/with space")
        with self.assertRaises(ValueError):
            MediaType("http://example.com")


class TestSignpost(unittest.TestCase):
    def testConstructorFromObjects(self):
        s = Signpost(
            LinkRel.cite_as,
            AbsoluteURI("http://example.com/pid/1"),
            MediaType("text/plain"),
            {AbsoluteURI("http://example.org/profileA"),
             AbsoluteURI("http://example.org/profileB")},
            AbsoluteURI("http://example.com/resource/1.html"))
        self.assertEqual("cite-as", s.rel.value)
        self.assertEqual("http://example.com/pid/1", str(s.target))
        self.assertEqual("text/plain", str(s.type))
        self.assertTrue(AbsoluteURI(
            "http://example.org/profileA") in s.profiles)
        self.assertTrue(AbsoluteURI(
            "http://example.org/profileB") in s.profiles)
        self.assertEqual("http://example.com/resource/1.html", str(s.context))
        self.assertIsNone(s.link)

    def testConstructorFromStrings(self):
        s = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            "text/plain",
            "http://example.org/profileA http://example.org/profileB",
            "http://example.com/resource/1.html")
        self.assertEqual("cite-as", s.rel.value)
        self.assertEqual("http://example.com/pid/1", str(s.target))
        self.assertEqual("text/plain", str(s.type))
        self.assertTrue(AbsoluteURI(
            "http://example.org/profileA") in s.profiles)
        self.assertTrue(AbsoluteURI(
            "http://example.org/profileB") in s.profiles)
        self.assertEqual("http://example.com/resource/1.html", str(s.context))
        self.assertIsNone(s.link)

    def testConstructorWithDefaults(self):
        s = Signpost(
            "cite-as",
            "http://example.com/pid/1")
        self.assertEqual("cite-as", s.rel.value)
        self.assertEqual("http://example.com/pid/1", str(s.target))
        self.assertIsNone(s.type)
        self.assertEqual(set(), s.profiles)
        self.assertIsNone(s.link)

    def testConstructorWithLink(self):
        link = Link("http://example.com/pid/1", [("rel", "cite-as")])
        s = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            link=link)
        self.assertEqual("cite-as", s.rel.value)
        self.assertEqual("http://example.com/pid/1", str(s.target))
        self.assertIsNone(s.type)
        self.assertEqual(set(), s.profiles)
        self.assertEqual(link, s.link)

    def testConstructorEmptyStrings(self):
        s = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            media_type="",
            profiles="")
        self.assertIsNone(s.type)
        self.assertEqual(set(), s.profiles)

    def testConstructorUnknownRel(self):
        with self.assertRaises(ValueError):
            s = Signpost(
                "stylesheet",
                "http://example.com/style.css")

    def testConstructorInvalidURI(self):
        with self.assertRaises(ValueError):
            s = Signpost(
                "cite-as",
                "10.1234/not-a-url")

    def testConstructorInvalidMediaType(self):
        with self.assertRaises(ValueError):
            s = Signpost(
                "item",
                "http://example.com/download/1.pdf",
                "pdf"  # should be "application/pdf"
                )

    def testConstructorInvalidProfiles(self):
        with self.assertRaises(ValueError):
            s = Signpost(
                "item",
                "http://example.com/download/1.pdf",
                profiles="https:/example.org/first-ok second-not-absolute"
                )

    def testConstructorHashProfile(self):
        target_url = "http://example.com/workflows/12/ro-crate-metadata.json"
        s = Signpost(
            LinkRel.describedby,
            target_url,
            "application/ld+json",
            # Multiple JSON-LD profiles with #hashes as in
            # https://www.researchobject.org/ro-crate/1.1/appendix/jsonld.html#ro-crate-json-ld-media-type
            "http://www.w3.org/ns/json-ld#flattened http://www.w3.org/ns/json-ld#compacted https://w3id.org/ro/crate")
        self.assertEqual("describedby", s.rel.value)
        self.assertEqual(target_url, str(s.target))
        self.assertEqual("application/ld+json", str(s.type))
        self.assertTrue(AbsoluteURI(
            "http://www.w3.org/ns/json-ld#flattened") in s.profiles)
        self.assertTrue(AbsoluteURI(
            "http://www.w3.org/ns/json-ld#compacted") in s.profiles)
        self.assertTrue(AbsoluteURI(
            "https://w3id.org/ro/crate") in s.profiles)
        self.assertEqual(3, len(s.profiles))
        self.assertIsNone(s.context, "Unexpected context")

    def testRepr(self):
        s = Signpost(
            LinkRel.cite_as,
            AbsoluteURI("http://example.com/pid/1"),
            MediaType("text/plain"),
            {AbsoluteURI("http://example.org/profileA"),
            AbsoluteURI("http://example.org/profileB")},
            AbsoluteURI("http://example.com/resource/1.html"))
        r = repr(s)
        self.assertIn("context=http://example.com/resource/1.html", r)
        self.assertIn("rel=cite-as", r)
        self.assertIn("target=http://example.com/pid/1", r)
        self.assertIn("type=text/plain", r)
        self.assertIn("profiles=http://example.org", r) # common URI prefix in this case
        self.assertIn("profileB", r)
        self.assertIn("profileA", r) # any order, as it's a set


    def testReprDefaults(self):
        s = Signpost(
            "cite-as",
            "http://example.com/pid/1")
        r = repr(s)
        self.assertIn("rel=cite-as", r)
        self.assertIn("target=http://example.com/pid/1", r)
        # Optional attributes hidden from repr()
        self.assertNotIn("context", r)
        self.assertNotIn("type", r)
        self.assertNotIn("profiles", r)

    def testEquals(self):
        s1 = Signpost(
            "cite-as",
            "http://example.com/pid/1")
        self.assertNotEqual(s1, 123) # Different type
        self.assertEqual(s1, Signpost("cite-as","http://example.com/pid/1"))
        self.assertEqual(s1, Signpost(LinkRel.cite_as, AbsoluteURI("http://example.com/pid/1")))
        self.assertNotEqual(s1, Signpost(LinkRel.author, AbsoluteURI("http://example.com/pid/1")))
        self.assertNotEqual(s1, Signpost(LinkRel.cite_as, AbsoluteURI("http://example.com/pid/2")))

        # For simplicity, any additional attributes make it unequal
        self.assertNotEqual(s1, Signpost("cite-as","http://example.com/pid/1", media_type="text/plain"))
        self.assertNotEqual(s1, Signpost("cite-as","http://example.com/pid/1", context="http://example.com/1.html"))
        self.assertNotEqual(s1, Signpost("cite-as","http://example.com/pid/1", profiles="http://example.com/profile/p1"))
        s2 = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            "text/plain",
            "http://example.org/profileA http://example.org/profileB",
            "http://example.com/resource/1.html")
        self.assertNotEqual(s1, s2)
        # signposts can also equal if all attributes equal
        self.assertEqual(s2,
            Signpost("cite-as","http://example.com/pid/1","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html"))
        # but if any of those attributes differ, they are also unequal.
        self.assertNotEqual(s2,  # rel
            Signpost("author","http://example.com/pid/1","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html"))
        self.assertNotEqual(s2, # target
            Signpost("cite-as","http://example.com/pid/2","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html"))
        self.assertNotEqual(s2, # media_type
            Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html"))
        self.assertNotEqual(s2, # profiles
            Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileC",
                "http://example.com/resource/1.html"))
        self.assertNotEqual(s2, # context
            Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/2.html"))
        # Note that profiles are a set, so this is still equal
        self.assertEqual(s2,
            Signpost("cite-as","http://example.com/pid/1","text/plain",
                "http://example.org/profileB http://example.org/profileA",
                "http://example.com/resource/1.html"))

    def testHash(self):
        """Basically same as testEquals, but using hash() of the signpost"""
        s1 = Signpost(
            "cite-as",
            "http://example.com/pid/1")

        self.assertEqual(hash(s1), hash(Signpost("cite-as","http://example.com/pid/1")))
        self.assertEqual(hash(s1), hash(Signpost(LinkRel.cite_as, AbsoluteURI("http://example.com/pid/1"))))
        self.assertNotEqual(hash(s1), hash(Signpost(LinkRel.author, AbsoluteURI("http://example.com/pid/1"))))
        self.assertNotEqual(hash(s1), hash(Signpost(LinkRel.cite_as, AbsoluteURI("http://example.com/pid/2"))))

        # For simplicity, any additional attributes make it unequal
        self.assertNotEqual(hash(s1), hash(Signpost("cite-as","http://example.com/pid/1", media_type="text/plain")))
        self.assertNotEqual(hash(s1), hash(Signpost("cite-as","http://example.com/pid/1", context="http://example.com/1.html")))
        self.assertNotEqual(hash(s1), hash(Signpost("cite-as","http://example.com/pid/1", profiles="http://example.com/profile/p1")))
        s2 = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            "text/plain",
            "http://example.org/profileA http://example.org/profileB",
            "http://example.com/resource/1.html")
        self.assertNotEqual(hash(s1), hash(s2))
        # signposts can also equal if all attributes equal
        self.assertEqual(hash(s2),
            hash(Signpost("cite-as","http://example.com/pid/1","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html")))
        # but if any of those attributes differ, they are also unequal.
        self.assertNotEqual(hash(s2),  # rel
            hash(Signpost("author","http://example.com/pid/1","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html")))
        self.assertNotEqual(hash(s2), # target
            hash(Signpost("cite-as","http://example.com/pid/2","text/plain",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html")))
        self.assertNotEqual(hash(s2), # media_type
            hash(Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/1.html")))
        self.assertNotEqual(hash(s2), # profiles
            hash(Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileC",
                "http://example.com/resource/1.html")))
        self.assertNotEqual(hash(s2), # context
            hash(Signpost("cite-as","http://example.com/pid/1","text/html",
                "http://example.org/profileA http://example.org/profileB",
                "http://example.com/resource/2.html")))
        # Note that profiles are a set, so this is still equal
        self.assertEqual(hash(s2),
            hash(Signpost("cite-as","http://example.com/pid/1","text/plain",
                "http://example.org/profileB http://example.org/profileA",
                "http://example.com/resource/1.html")))

        # We'll knowingly permit hashes to ignore ordering of attributes,
        # as they are unlikely to overlap in actual signposts. Here we deliberately make two "opposing"
        # signposts and see if they get the same hash as they'll have swapped
        # target/context URIs. Implementation of Signpost are allowed
        # to break this optimization, in which case the below test should be removed.
        s2a = Signpost("cite-as","http://example.com/resource/1.html","text/plain",
                "http://example.org/profileB http://example.org/profileA",
                "http://example.com/pid/1")
        self.assertEqual(hash(s2), hash(s2a))
        # However these signposts are still unequal,
        # even if they have same hash. Hashes do not need to be
        # unique, just unlikely to be so for different objects
        self.assertNotEqual(s2, s2a)

    def testWithContext(self):
        s1 = Signpost(
            "cite-as",
            "http://example.com/pid/1",
            "text/plain",
            "http://example.org/profileA http://example.org/profileB",
            "http://example.com/resource/1.html")
        s1Same = s1.with_context(s1.context)
        self.assertEqual(s1, s1Same)
        self.assertEqual(s1.context, s1Same.context)

        s2 = s1.with_context("http://example.com/resource/1.rdf")
        self.assertIsInstance(s2.context, AbsoluteURI)
        self.assertEqual(AbsoluteURI("http://example.com/resource/1.rdf"), s2.context)
        self.assertNotEqual(s1, s2) # as context is different
        self.assertEqual(s1, s2.with_context(s1.context)) ## but if we change back 100% same

        s3 = s1.with_context(None)
        self.assertNotEqual(s1, s3)
        self.assertIsNone(s3.context)
        self.assertEqual(s1, s3.with_context(s1.context))


class TestSignposting(unittest.TestCase):
    def testConstructorDefault(self):
        s = Signposting("http://example.com/page1")
        self.assertEqual("http://example.com/page1", s.context)
        self.assertIsNone(s.citeAs)
        self.assertIsNone(s.license)
        self.assertIsNone(s.collection)
        self.assertEqual(set(), s.authors)
        self.assertEqual(set(), s.describedBy)
        self.assertEqual(set(), s.items)
        self.assertEqual(set(), s.linksets)
        self.assertEqual(set(), s.types)

    def testReprDefault(self):
        s = Signposting("http://example.com/page1")
        r = repr(s)
        self.assertIn("context=http://example.com/page1", r)
        # Defaults hidden in repr()
        self.assertNotIn("None", r)

    def testStrDefault(self):
        s = Signposting("http://example.com/page1")
        self.assertEqual("", str(s)) # empty, no Link headers

    def testConstructorEmpty(self):
        s = Signposting("http://example.com/page1", [])
        self.assertEqual("http://example.com/page1", s.context)
        self.assertIsNone(s.citeAs)
        self.assertEqual(set(), s.types)

    def testConstructorValueError(self):
        with self.assertRaises(ValueError):
            Signposting(signposts=[
                Signpost(LinkRel.cite_as, "http://example.com/pid/1")
            ], include_no_context=False)

    def testConstructorUnrecognizedRel(self):
        # Evil hack to pretend LinkRel has a new relation
        FakeLinkRel = Enum("LinkRel",
            itertools.chain(
                [("fake", "fake")],
                [(a,a) for a in LinkRel.__members__]
            ),
            type=str)
        try:
            # Fake-inject of new enum class
            signposting.signpost.LinkRel = FakeLinkRel
            with warnings.catch_warnings(record=True) as w:
                unrecognized = Signposting(signposts=[
                    Signpost("fake", "http://example.com/fake"),
                    Signpost("type", "http://example.com/type/Example"),
                ])
        finally:
            # Restore the proper enum
            signposting.signpost.LinkRel = LinkRel

        # Ensure that raised a warning!
        self.assertEqual(1, len(w))
        self.assertTrue(issubclass(w[0].category, UserWarning))
        self.assertIn("fake", str(w[0].message))
        # And that "fake" was not thrown away
        self.assertTrue(unrecognized.types)
        self.assertEqual({"http://example.com/type/Example"},
                          {s.target for s in unrecognized.types})
        self.assertEqual({"http://example.com/fake", "http://example.com/type/Example"},
                          {s.target for s in unrecognized})

    def testConstructorCiteAs(self):
        s = Signposting("http://example.com/page1",
                        [Signpost(LinkRel.cite_as, "http://example.com/pid/1")]
                        )
        self.assertEqual("http://example.com/page1", s.context)
        self.assertEqual(AbsoluteURI(
            "http://example.com/pid/1"), s.citeAs.target)

    def testReprCiteAs(self):
        r = repr(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.cite_as, "http://example.com/pid/1")]))
        self.assertIn("citeAs=http://example.com/pid/1", r)
            # Matches camel-case attribute name, not link relation or LinkRel enum..
            # FIXME: Avoid 3 variations!
        self.assertIn("context=http://example.com/page1", r)

    def testStrCiteAs(self):
        s = str(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.cite_as, "http://example.com/pid/1")]))
        self.assertEqual("Link: <http://example.com/pid/1>; rel=cite-as", s)

    def testStrItemType(self):
        s = str(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.item, "http://example.com/file/2.txt", media_type=MediaType("text/plain"))]))
        self.assertEqual('Link: <http://example.com/file/2.txt>; rel=item; type="text/plain"', s)

    def testStrDescribedbyProfile(self):
        s = str(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.describedby, "http://example.com/file/meta.ttl",
                    media_type=MediaType("text/turtle"),
                    profiles="http://example.com/profile/1")]))
        self.assertEqual('Link: <http://example.com/file/meta.ttl>; rel=describedby; '
            'type="text/turtle"; profile="http://example.com/profile/1"', s)

    def testStrItemContext(self):
        s = str(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.item, "http://example.com/file/2.txt", context="http://example.com/page1")]))
        # Notice context is called anchor
        self.assertEqual('Link: <http://example.com/file/2.txt>; rel=item; anchor="http://example.com/page1"', s)

    def testStrItemOtherContext(self):
        s = str(Signposting("http://example.com/page1",
                 [Signpost(LinkRel.item, "http://example.com/file/2.txt", context="http://example.com/page2")]))
        # NOTE: All signposts are included in str()
        self.assertEqual('Link: <http://example.com/file/2.txt>; rel=item; anchor="http://example.com/page2"', s)

    def testConstructorItems(self):
        s = Signposting("http://example.com/page1", [
            Signpost(LinkRel.item, "http://example.com/item/1.pdf"),
            Signpost(LinkRel.item, "http://example.com/item/2.txt")])
        self.assertEqual({"http://example.com/item/1.pdf", "http://example.com/item/2.txt"},
                         set(str(i.target) for i in s.items))

    def testConstructorComplete(self):
        s = Signposting("http://example.com/page1", [
            Signpost(LinkRel.item, "http://example.com/item/1.pdf"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            # tip: order does not matter
            Signpost(LinkRel.item, "http://example.com/item/2.txt"),
            Signpost(LinkRel.license, "http://spdx.org/licenses/CC0-1.0"),
            Signpost(LinkRel.collection, "http://example.com/collection/1"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
            Signpost(LinkRel.describedby, "http://example.com/metadata/1.ttl"),
            Signpost(LinkRel.describedby,
                     "http://example.com/metadata/2.jsonld"),
            Signpost(LinkRel.describes,
                     "http://example.com/other"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/1.json"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/2.txt"),
            Signpost(LinkRel.type, "http://example.org/type/A"),
            Signpost(LinkRel.type, "http://example.org/type/B")
            ])

        self.assertEqual("http://example.com/page1", s.context)
        self.assertEqual(AbsoluteURI(
            "http://example.com/pid/1"), s.citeAs.target)
        self.assertEqual(AbsoluteURI(
            "http://spdx.org/licenses/CC0-1.0"), s.license.target)
        self.assertEqual(AbsoluteURI(
            "http://example.com/collection/1"), s.collection.target)
        self.assertEqual({
            "http://example.com/item/1.pdf",
            "http://example.com/item/2.txt"},
            set(i.target for i in s.items))
        self.assertEqual({
            "http://example.com/author/1",
            "http://example.com/author/2"},
            set(i.target for i in s.authors))
        self.assertEqual({
            "http://example.com/metadata/1.ttl",
            "http://example.com/metadata/2.jsonld"},
            set(i.target for i in s.describedBy))
        self.assertEqual({"http://example.com/other"},
                         {i.target for i in s.describes})
        self.assertEqual({
            "http://example.com/linkset/1.json",
            "http://example.com/linkset/2.txt"},
            set(i.target for i in s.linksets))
        self.assertEqual({
            "http://example.org/type/A",
            "http://example.org/type/B"},
            set(i.target for i in s.types))

    def testReprComplete(self):
        s = Signposting("http://example.com/page1", [
            Signpost(LinkRel.item, "http://example.com/item/1.pdf"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            # tip: order does not matter
            Signpost(LinkRel.item, "http://example.com/item/2.txt"),
            Signpost(LinkRel.license, "http://spdx.org/licenses/CC0-1.0"),
            Signpost(LinkRel.collection, "http://example.com/collection/1"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
            Signpost(LinkRel.describedby, "http://example.com/metadata/1.ttl"),
            Signpost(LinkRel.describedby,
                     "http://example.com/metadata/2.jsonld"),
            Signpost(LinkRel.describes,
                     "http://example.com/other"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/1.json"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/2.txt"),
            Signpost(LinkRel.type, "http://example.org/type/A"),
            Signpost(LinkRel.type, "http://example.org/type/B"),
            Signpost(LinkRel.item, "http://example.com/item/3.jpeg", context="http://example.com/page3"),
            Signpost(LinkRel.item, "http://example.com/item/4.jpeg", context="http://example.com/page4"),

            ])
        r = repr(s)
        self.assertIn("context=http://example.com/page1", r)
        self.assertIn("items=http://example.com/item/", r)
        self.assertIn("item/1.pdf", r)
        self.assertIn("item/2.txt", r)
        self.assertIn("citeAs=http://example.com/pid/1", r)
        self.assertIn("license=http://spdx.org/licenses/CC0-1.0", r)
        self.assertIn("collection=http://example.com/collection/1", r)
        self.assertIn("authors=http://example.com/author/", r)
        self.assertIn("/author/1", r) # Order may not be preserved (?)
        self.assertIn("/author/2", r)
        self.assertIn("describedBy=http://example.com/metadata", r)
        self.assertIn("metadata/1.ttl",r)
        self.assertIn("metadata/2.jsonld", r)
        self.assertIn("describes", r)
        self.assertIn("http://example.com/other", r)
        self.assertIn("linksets=http://example.com/linkset", r)
        self.assertIn("linkset/1.json",r)
        self.assertIn("linkset/2.txt", r)
        self.assertIn("types=http://example.org/type", r)
        self.assertIn("type/A",r)
        self.assertIn("type/B", r)
        self.assertIn("other_contexts=http://example.com/page", r)
        self.assertIn("page3", r)
        self.assertIn("page4", r)
        self.assertNotIn("item/3.jpeg", r)
        self.assertNotIn("item/4.jpeg", r)

    def testIterComplete(self):
        signposts = {
            Signpost(LinkRel.item, "http://example.com/item/1.pdf"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            Signpost(LinkRel.item, "http://example.com/item/2.txt"),
            Signpost(LinkRel.license, "http://spdx.org/licenses/CC0-1.0"),
            Signpost(LinkRel.collection, "http://example.com/collection/1"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
            Signpost(LinkRel.describedby, "http://example.com/metadata/1.ttl"),
            Signpost(LinkRel.describedby,
                     "http://example.com/metadata/2.jsonld"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/1.json"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/2.txt"),
            Signpost(LinkRel.type, "http://example.org/type/A"),
            Signpost(LinkRel.type, "http://example.org/type/B"),
            Signpost(LinkRel.describes, "http://example.com/other"),
            Signpost(AbsoluteURI("https://schema.org/identifier"),  "urn:uuid:3d40f08b-0faa-4169-b329-3d6779bbffee")
        }
        # Ensure THIS test has tested every type of LinkRel!
        self.assertEqual(set(LinkRel), {s.rel for s in signposts if isinstance(s.rel, LinkRel)})

        others = {
            Signpost(LinkRel.item, "http://example.com/item/3.jpeg", context="http://example.com/page3"),
            Signpost(LinkRel.item, "http://example.com/item/4.jpeg", context="http://example.com/page4"),
        }
        signposting = Signposting("http://example.com/page1", signposts|others)
        iterated = {s for s in signposting}
        self.assertEqual(signposts, iterated) # Excluding others
        # here they all are!
        self.assertEqual(signposts|others, signposting.signposts)

    def testReprSimple(self):
        s = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/1")
        ])
        r = repr(s)
        self.assertIn("citeAs=http://example.com/pid/1", r)
        self.assertNotIn("context=", r)
        self.assertNotIn("items=", r)
        self.assertNotIn("license=", r)
        self.assertNotIn("collection=", r)
        self.assertNotIn("authors=", r)
        self.assertNotIn("describedBy=", r)
        self.assertNotIn("linksets=", r)
        self.assertNotIn("types=", r)
        self.assertNotIn("other_contexts=", r)

    def testConstructorWarnDuplicate(self):
        with warnings.catch_warnings(record=True) as w:
            s = Signposting("http://example.com/page1", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
                Signpost(LinkRel.cite_as, "http://example.com/pid/2-ignored"),
                Signpost(LinkRel.license, "http://spdx.org/licenses/CC0-1.0"),
                Signpost(LinkRel.license, "https://creativecommons.org/publicdomain/zero/1.0/legalcode"),
                Signpost(LinkRel.collection, "http://example.com/collection/1"),
                Signpost(LinkRel.collection, "http://example.com/collection/2"),
                ])

            self.assertEqual(3, len(w))
            # Only first signpost should be kept
            self.assertEqual(
                "http://example.com/pid/1", s.citeAs.target)
            self.assertEqual(
                "http://spdx.org/licenses/CC0-1.0", s.license.target)
            self.assertEqual(
                "http://example.com/collection/1", s.collection.target)


    def testNoneContextWarns(self):
        with warnings.catch_warnings(record=True) as w:
            s = Signposting(None, [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page2"),
                Signpost(LinkRel.cite_as, "http://example.com/pid/1", context="http://example.com/page1"),
                ])
        # First cite_as is picked, ignoring context or not
        self.assertEqual("http://example.com/pid/2", s.citeAs.target)
        self.assertEqual(1, len(w))
        self.assertTrue(issubclass(w[0].category, UserWarning))
        self.assertIn("cite-as", str(w[0].message))

    def testNoneContextMixed(self):
        with warnings.catch_warnings(record=True) as w2:
            s2 = Signposting(None, [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page2"),
                Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
                ])
        # Even here, as "None" context means any signposts.
        # They are not ordered in any priority, first one wins.
        self.assertEqual("http://example.com/pid/2", s2.citeAs.target)
        self.assertEqual(1, len(w2))
        self.assertTrue(issubclass(w2[0].category, UserWarning))
        self.assertIn("cite-as", str(w2[0].message))

    def testContextMixed(self):
        # However, in this case we have a known context, which will be
        # assigned to pid/1, pid/2 is ignored as it has a different context
        s3 = Signposting("http://example.com/page1", [
            Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page2"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            ])
        self.assertEqual("http://example.com/pid/1", s3.citeAs.target)

    def testIncludeNoContextNoMatch(self):
        # ..unlexs we override to ignore signposts with no context
        s4 = Signposting("http://example.com/page1", [
            Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page2"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            ], include_no_context=False)
        self.assertIsNone(s4.citeAs)

    def testIncludeNoContextMatch(self):
        s5 = Signposting("http://example.com/page3", [
            Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page2"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/1"),
            Signpost(LinkRel.cite_as, "http://example.com/pid/3", context="http://example.com/page3"),
            ], include_no_context=False)
        # In this case, context must match for every signpost
        self.assertEqual("http://example.com/pid/3", s5.citeAs.target)
        self.assertEqual(1, len(s5))

    def testForContext(self):
        s = Signposting("http://example.com/page1", [
            Signpost(LinkRel.author, "http://example.com/author/1"),
            Signpost(LinkRel.author, "http://example.com/author/2", context="http://example.com/page2"),
            Signpost(LinkRel.author, "http://example.com/author/3", context="http://example.com/page3"),
            ])
        self.assertEqual(1, len(s)) # Ignores page2, page3
        self.assertEqual({"http://example.com/page2", "http://example.com/page3"},
            s.other_contexts
        )
        s2 = s.for_context("http://example.com/page2")
        s3 = s.for_context("http://example.com/page3")
        s4 = s.for_context("http://example.com/page4")
        self.assertTrue(s2)
        self.assertTrue(s3)
        self.assertFalse(s4)
        self.assertEqual({"http://example.com/author/2"}, {a.target for a in s2.authors})
        self.assertEqual({"http://example.com/author/3"}, {a.target for a in s3.authors})

        # The other contexts are carried on
        self.assertTrue(s3.for_context("http://example.com/page2"))
        self.assertTrue(s2.for_context("http://example.com/page3"))
        # Ensure we have not lost the author/1 link with implicit context of page1
        sAgain = s2.for_context("http://example.com/page1")
        self.assertTrue(sAgain)
        self.assertEqual({"http://example.com/author/1"},
            {a.target for a in sAgain.authors})
        # But now with explicit context
        self.assertEqual({"http://example.com/page1"},
            {a.context for a in sAgain.authors})

        # We can get them all in one go
        sAll = s.for_context(None)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2", "http://example.com/author/3"},
            {a.target for a in sAll.authors})
        # author/1 should be in here
        sNoContext = {sign for sign in s.signposts if not sign.context}
        self.assertTrue(sNoContext)
        self.assertEqual({"http://example.com/author/1"}, {a.target for a in sNoContext})
        # However in s2 it has been given an explicit context, so
        # no signposts remains without context
        s2NoContext = {sign for sign in sAgain.signposts if not sign.context}
        self.assertFalse(s2NoContext)

        # Tip, here's another way we can get ONLY the Defaults:
        # use a brand new context
        defaultsOnly = Signposting(uuid.uuid4().urn, s.signposts)
        self.assertTrue(defaultsOnly)
        self.assertEqual({"http://example.com/author/1"}, {a.target for a in defaultsOnly.authors})


    def testLengthIgnoresWrongContext(self):
        s = Signposting("http://example.com/page3", [
            Signpost(LinkRel.author, "http://example.com/author/1"),
            Signpost(LinkRel.author, "http://example.com/author/2", context="http://example.com/page2"),
            Signpost(LinkRel.author, "http://example.com/author/3", context="http://example.com/page3"),
            ])
        self.assertEqual(2, len(s)) # Ignores page2
        # The remaining signpost is under another context, which would ignore
        # author/1 (assigned to default context page3)
        self.assertEqual(1, len(s.for_context("http://example.com/page2")))

    def testEqualsEmptySignposts(self):
        self.assertEqual( # empty list of signposts
            Signposting("http://example.com/page3", []),
            Signposting("http://example.com/page3", [])
        )
    def testEqualsEmptyDifferentContext(self):
        self.assertEqual( # empty list of signposts, but we're different context
            Signposting("http://example.com/page3", []),
            Signposting("http://example.com/OTHER", [])
        )
    def testEqualsCiteAs(self):
        self.assertEqual( # single signpost equals
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ]),
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ])
        )

    def testEqualsAnyOrder(self):
        self.assertEqual( # multiple signpost in any order
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2"),
                Signpost(LinkRel.author, "http://example.com/author/1"),
                Signpost(LinkRel.author, "http://example.com/author/2"),
            ]),
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.author, "http://example.com/author/1"),
                Signpost(LinkRel.cite_as, "http://example.com/pid/2"),
                Signpost(LinkRel.author, "http://example.com/author/2"),
            ])
        )

    def testNotEqualsMissingAuthor(self):
        self.assertNotEqual(
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.author, "http://example.com/author/1"),
                Signpost(LinkRel.author, "http://example.com/author/2"),
                Signpost(LinkRel.author, "http://example.com/author/3"),
            ]),
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.author, "http://example.com/author/1"),
                Signpost(LinkRel.author, "http://example.com/author/2"),
            ])
        )

    def testNotEqualsCiteAsDiffers(self):
        self.assertNotEqual( # single signpost differs
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ]),
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/OTHER")
            ])
        )
    def testEqualsCiteAsExplicitContext(self):
        self.assertEqual( # single signpost differs with same context
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page3")
            ]),
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page3")
            ])
        )
    def testNotEqualsCiteAsImplicitContext(self):
        # signposts are effectively same context, however
        # Signposting.__eq__ is defined to always take s.context into consideration
        self.assertNotEqual(
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2",
                context="http://example.com/page3")
            ]),
            Signposting("http://example.com/page3", [
                # Implicit context, inherited
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ])
        )
    def testEqualsCiteAsContextMadeExplicit(self):
        # Force them to be equal
        self.assertEqual(
            Signposting("http://example.com/page3", [
                Signpost(LinkRel.cite_as, "http://example.com/pid/2",
                context="http://example.com/page3")
            ]),
            Signposting("http://example.com/page3", [
                # Implicit context, inherited
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ]).for_context("http://example.com/page3") # made explicit
        )


    def testNotEqualsCiteAsDifferentContext(self):
        self.assertNotEqual( # single signpost differs because different context
            Signposting(signposts=[
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page3")
            ]),
            Signposting(signposts=[
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/OTHER")
            ])
        )
    def testNotEqualsCiteAsMissingContext(self):
        self.assertNotEqual( # single signpost differs because second is missing context
            Signposting(signposts=[
                Signpost(LinkRel.cite_as, "http://example.com/pid/2", context="http://example.com/page4")
            ]),
            Signposting(signposts=[
                # FIXME: This should inherit the above context, but the above had explicit page4
                Signpost(LinkRel.cite_as, "http://example.com/pid/2")
            ])
        )

    def testMergeWrongType(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = [
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ]
        with self.assertRaises(TypeError):
            c = a | b
        # .. as B is not instance of Signposting with unknown context, it can't be merged

    def testMergeNoContext(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a|b
        self.assertIsNone(c.context)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertIn("http://example.com/pid/A", {s.target for s in c})
        self.assertIn("http://example.com/pid/B", {s.target for s in c})
        self.assertEqual(a.citeAs.target, c.citeAs.target) # original PID target from A survives
        # without any rewritten context
        self.assertIsNone(c.citeAs.context)
        # this mean by Signpost.__eq__ they ARE the same signpost
        self.assertEqual(a.citeAs, c.citeAs)
        # union of author sets
        self.assertEqual(a.authors | b.authors, c.authors)

    def testMergeSameContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a|b
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertIn("http://example.com/pid/A", {s.target for s in c})
        self.assertIn("http://example.com/pid/B", {s.target for s in c})
        self.assertEqual(a.citeAs.target, c.citeAs.target) # original PID target from A survives
        # but now rewritten to explicit context
        self.assertEqual("http://example.com/doc1", c.citeAs.context)
        # NOTE: this mean by Signpost.__eq__ they are not the same signpost
        self.assertNotEqual(a.citeAs, c.citeAs)

    def testMergeNewContext(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a|b
        # as A didn't have a context
        self.assertEqual(b.context, c.context)
        self.assertEqual({"http://example.com/author/2"},
            {a.target for a in c.authors})

        # as that is the PID of the existing context
        self.assertEqual("http://example.com/pid/B", c.citeAs.target)
        # Now with explicit context
        self.assertEqual("http://example.com/doc1", c.citeAs.context)
        self.assertEqual(2, len(c)) # as only doc1 is focus by the determined context
        # They didn't match context
        self.assertNotIn("http://example.com/pid/A", {s.target for s in c})
        self.assertNotIn("http://example.com/author/1", {s.target for s in c})
        # But they survive here
        self.assertIn("http://example.com/pid/A", {s.target for s in c.signposts})
        self.assertIn("http://example.com/author/1", {s.target for s in c.signposts})
        # Their context was NOT rewritten as there was nothing to assign
        self.assertEqual({None}, {s.context for s in c.signposts if s.target=="http://example.com/pid/A"})
        self.assertEqual({None}, {s.context for s in c.signposts if s.target=="http://example.com/author/1"})

    def testMergeOtherContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(context="http://example.com/doc2", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a|b
        # A's context is preferred if set
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1"},
            {a.target for a in c.authors})
        # as that is the PID of the existing context
        self.assertEqual("http://example.com/pid/A", c.citeAs.target)
        # Now with explicit context
        self.assertEqual("http://example.com/doc1", c.citeAs.context)
        self.assertEqual(2, len(c)) # as only doc1 is focus by the determined context
        # They didn't match context
        self.assertNotIn("http://example.com/pid/B", {s.target for s in c})
        self.assertNotIn("http://example.com/author/2", {s.target for s in c})
        # But they survive here:
        self.assertEqual({"http://example.com/doc2"}, c.other_contexts)
        # Their context WAS rewritten
        self.assertEqual("http://example.com/pid/B", c.for_context("http://example.com/doc2").citeAs.target)
        self.assertEqual({"http://example.com/author/2"}, {a.target for a in c.for_context("http://example.com/doc2").authors})
        ## this should (in this particular case) mean:
        self.assertEqual(b.for_context("http://example.com/doc2"), c.for_context("http://example.com/doc2"))
        # and even:
        self.assertEqual(a.for_context("http://example.com/doc1"), c.for_context("http://example.com/doc1"))
        ## NOTE: We had to use for_context above to compare their Signpost's using explicit contexts


    def testMergeDefaultContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a|b
        # as B didn't have a context
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1"},
            {a.target for a in c.authors})

        # as that is the PID of the existing context
        self.assertEqual("http://example.com/pid/A", c.citeAs.target)
        # Now with explicit context
        self.assertEqual("http://example.com/doc1", c.citeAs.context)
        self.assertEqual(2, len(c)) # as only doc1 is focus by the determined context
        # They didn't match context
        self.assertNotIn("http://example.com/pid/B", {s.target for s in c})
        self.assertNotIn("http://example.com/author/2", {s.target for s in c})
        # But they survive here:
        self.assertIn("http://example.com/pid/B", {s.target for s in c.signposts})
        self.assertIn("http://example.com/author/2", {s.target for s in c.signposts})


    def testAddIterable(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = {
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        } # order does not matter
        c = a+b
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertEqual("http://example.com/pid/B", c.citeAs.target)
        self.assertEqual(4, len(c)) # including relegated pid/A
        self.assertIn("http://example.com/pid/A", {s.target for s in c})

    def testAddNoContext(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a+b
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertEqual("http://example.com/pid/B", c.citeAs.target)
        self.assertEqual(4, len(c)) # including relegated pid/A
        self.assertIn("http://example.com/pid/A", {s.target for s in c})

    def testAddOldContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
        ])
        c = a+b
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertEqual("http://example.com/pid/B", c.citeAs.target)
        self.assertEqual(4, len(c)) # including relegated pid/A
        self.assertIn("http://example.com/pid/A", {s.target for s in c})

    def testAddSameContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2"),
            Signpost(LinkRel.author, "http://example.com/author/3", context="http://example.com/doc3"),
        ])
        c = a+b
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertEqual("http://example.com/pid/B", c.citeAs.target)
        self.assertEqual(4, len(c)) # including relegated pid/A
        self.assertIn("http://example.com/pid/A", {s.target for s in c})
        # NOT added as it was in wrong context
        self.assertNotIn("http://example.com/author/3", {s.target for s in c.signposts})

    def testAddDifferentContext(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1"),
        ])
        b = Signposting(context="http://example.com/doc2", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/B"),
            Signpost(LinkRel.author, "http://example.com/author/2", context="http://example.com/doc1"),
            Signpost(LinkRel.author, "http://example.com/author/3")
        ])
        c = a+b
        self.assertEqual(a.context, c.context)
        self.assertEqual({"http://example.com/author/1", "http://example.com/author/2"},
            {a.target for a in c.authors})
        self.assertEqual("http://example.com/pid/A", c.citeAs.target)
        self.assertEqual(3, len(c)) # IGNORING pid/B as it's got wrong context
        # These were NOT added as they were not in the current context
        self.assertNotIn("http://example.com/pid/B", {s.target for s in c.signposts})
        self.assertNotIn("http://example.com/author/3", {s.target for s in c.signposts})

    def test_signposts_with_explicit_context(self):
        a = Signposting(context="http://example.com/doc1", signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1", context="http://example.com/doc2"),
        ])
        explicitA = set(a._signposts_with_explicit_context())
        self.assertEqual({"http://example.com/pid/A", "http://example.com/author/1"},
            {s.target for s in explicitA})
        # All signposts now have explicit context
        self.assertEqual({"http://example.com/doc1", "http://example.com/doc2"}, {s.context for s in explicitA})

    def test_signposts_with_explicit_context_warning_implicit(self):
        a = Signposting(signposts=[
            Signpost(LinkRel.cite_as, "http://example.com/pid/A"),
            Signpost(LinkRel.author, "http://example.com/author/1", context="http://example.com/doc2"),
        ])
        explicitA = set(a._signposts_with_explicit_context())
        self.assertEqual({"http://example.com/pid/A", "http://example.com/author/1"},
            {s.target for s in explicitA})
        # In this case we still had to keep the empty context
        self.assertEqual({None, "http://example.com/doc2"}, {s.context for s in explicitA})

    def test_signposts_with_explicit_context_warning(self):
        b = Signposting(context="http://example.com/doc1",
            signposts=[
                Signpost(LinkRel.cite_as, "http://example.com/pid/A", context="http://example.com/doc1"),
                Signpost(LinkRel.author, "http://example.com/author/1"),
            ],
            include_no_context=False) # author moved to self._others

        with warnings.catch_warnings(record=True) as warningsRaised:
            explicitB = set(b._signposts_with_explicit_context())
        self.assertEqual({"http://example.com/pid/A"},
            {s.target for s in explicitB}) # author/1 IGNORED
        self.assertTrue(warningsRaised)

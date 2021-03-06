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

import unittest
import warnings

from httplink import Link

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
            # This is the maximum permissable
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


class TestSignPost(unittest.TestCase):
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


class TestSignposting(unittest.TestCase):
    def testConstructorDefault(self):
        s = Signposting("http://example.com/page1")
        self.assertEqual("http://example.com/page1", s.context_url)
        self.assertIsNone(s.citeAs)
        self.assertIsNone(s.license)
        self.assertIsNone(s.collection)
        self.assertEqual(set(), s.authors)
        self.assertEqual(set(), s.describedBy)
        self.assertEqual(set(), s.items)
        self.assertEqual(set(), s.linksets)
        self.assertEqual(set(), s.types)

    def testConstructorEmpty(self):
        s = Signposting("http://example.com/page1", [])
        self.assertEqual("http://example.com/page1", s.context_url)
        self.assertIsNone(s.citeAs)
        self.assertEqual(set(), s.types)

    def testConstructorCiteAs(self):
        s = Signposting("http://example.com/page1",
                        [Signpost(LinkRel.cite_as, "http://example.com/pid/1")]
                        )
        self.assertEqual("http://example.com/page1", s.context_url)
        self.assertEqual(AbsoluteURI(
            "http://example.com/pid/1"), s.citeAs.target)

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
            Signpost(LinkRel.linkset, "http://example.com/linkset/1.json"),
            Signpost(LinkRel.linkset, "http://example.com/linkset/2.txt"),
            Signpost(LinkRel.type, "http://example.org/type/A"),
            Signpost(LinkRel.type, "http://example.org/type/B")
            ])

        self.assertEqual("http://example.com/page1", s.context_url)
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
        self.assertEqual({
            "http://example.com/linkset/1.json",
            "http://example.com/linkset/2.txt"},
            set(i.target for i in s.linksets))
        self.assertEqual({
            "http://example.org/type/A",
            "http://example.org/type/B"},
            set(i.target for i in s.types))

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
            

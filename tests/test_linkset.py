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
"""Test linkset parsing according to RFC9264."""

import warnings
import unittest
from urllib.error import HTTPError
import requests
import requests_mock
import importlib.resources
import os

from signposting import linkset
from signposting.resolver import find_signposting_http
from signposting.signpost import AbsoluteURI, MediaType

a2a_27 = importlib.resources.read_text("tests.data.a2afairmetrics", "27-http-linkset-json-only.json")
a2a_28 = importlib.resources.read_text("tests.data.a2afairmetrics", "28-http-linkset-txt-only.txt")

class TestDownloadedText(unittest.TestCase):
    def test_linkset(self):
        ls = linkset.Linkset('''<https://w3id.org/a2a-fair-metrics/28-http-linkset-txt-only/>
 ; anchor="https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/"
 ; rel="cite-as"
''', 
            "application/linkset",
            AbsoluteURI("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt"),
            AbsoluteURI("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt")
        )
        self.assertIn('rel="cite-as', ls)

class TestParseLinkset(unittest.TestCase):
    def test_parse_linkset_a2a_28(self):
        ls = linkset.Linkset(a2a_28, "application/linkset", 
            AbsoluteURI("https://s11.example.net/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt"),
            AbsoluteURI("https://s11.example.net/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt"))
        signposts = linkset._parse_linkset(ls)
        self.assertEqual("https://s11.example.net/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt", signposts.context_url)
        
        self.assertEqual("https://w3id.org/a2a-fair-metrics/28-http-linkset-txt-only/", signposts.citeAs.target)

        self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/index.ttl"},
            {d.target for d in signposts.describedBy})
        self.assertEqual({"text/turtle"},
            {d.type for d in signposts.describedBy})

        self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/test-apple-data.csv"},
            {i.target for i in signposts.items})
        self.assertEqual({"text/csv"},
            {i.type for i in signposts.items})

        self.assertEqual(3, len(signposts))
        # Assert context is picked up from anchor=""
        for s in signposts:
            self.assertEqual("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/", s.context)

    def test_parse_linkset_a2a_27(self):
        ls = linkset.LinksetJSON(a2a_27, "application/linkset+json", 
            AbsoluteURI("https://s11.example.net/2022/a2a-fair-metrics/27-http-linkset-json-only/linkset.json"),
            AbsoluteURI("https://s11.example.net/2022/a2a-fair-metrics/27-http-linkset-json-only/linkset.json"))
        signposts = linkset._parse_linkset_json(ls)
        self.assertEqual("https://s11.example.net/2022/a2a-fair-metrics/27-http-linkset-json-only/linkset.json", signposts.context_url)
        
        self.assertEqual("https://w3id.org/a2a-fair-metrics/27-http-linkset-json-only/", signposts.citeAs.target)
        
        self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/index.ttl"},
            {d.target for d in signposts.describedBy})
        self.assertEqual({"text/turtle"},
            {d.type for d in signposts.describedBy})

        self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/test-apple-data.csv"},
            {i.target for i in signposts.items})
        self.assertEqual({"text/csv"},
            {i.type for i in signposts.items})

        self.assertEqual(3, len(signposts))
        # Assert context is picked up from "anchor"
        for s in signposts:
            self.assertEqual("https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/", s.context)


@unittest.skipIf(os.environ.get("CI"), "Integration tests requires network access")
class TestFindSignpostingLinkset(unittest.TestCase):

    def _linksets_for_pid(self, pid):
        # We'll use signposting to find the linkset URI
        pre_signposts = find_signposting_http(pid)
        self.assertTrue(pre_signposts.linksets, "No signposts to linksets found for %s" % pid)
        return [(l.target,l.type) for l in pre_signposts.linksets]

    def test_parse_linkset_a2a_07(self):
        PID = "https://w3id.org/a2a-fair-metrics/07-http-describedby-citeas-linkset-json/"
        for (uri,_) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri)
            self.assertEqual(uri, signposts.context_url)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/07-http-describedby-citeas-linkset-json/", 
                signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/07-http-describedby-citeas-linkset-json/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/07-http-describedby-citeas-linkset-json/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor=""
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/07-http-describedby-citeas-linkset-json/", 
                s.context)

    def test_parse_linkset_a2a_08(self):
        PID = "https://w3id.org/a2a-fair-metrics/08-http-describedby-citeas-linkset-txt/"
        for (uri,_) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri)
            self.assertEqual(uri, signposts.context_url)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/08-http-describedby-citeas-linkset-txt/", 
                signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/08-http-describedby-citeas-linkset-txt/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/08-http-describedby-citeas-linkset-txt/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor=""
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/08-http-describedby-citeas-linkset-txt/", 
                s.context)

    def test_parse_linkset_a2a_09(self):
        PID = "https://w3id.org/a2a-fair-metrics/09-http-describedby-citeas-linkset-json-txt/"
        linksets = self._linksets_for_pid(PID)
        for (uri,mediatype) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri, mediatype)

            self.assertEqual(uri, signposts.context_url)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/09-http-describedby-citeas-linkset-json-txt/", 
                signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/09-http-describedby-citeas-linkset-json-txt/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/09-http-describedby-citeas-linkset-json-txt/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor=""
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/09-http-describedby-citeas-linkset-json-txt/", 
                s.context)

    def test_parse_linkset_a2a_14(self):
        PID = "https://w3id.org/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/"
        for (uri,mediatype) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri, mediatype)
            if mediatype == MediaType("application/linkset+json"):
                # Ensure Content-Location was picked up even if "uri" stayed the same
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/linkset.json", 
                    signposts.context_url)
            elif mediatype == MediaType("application/linkset"):
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/linkset.txt", 
                    signposts.context_url)
            else:
                raise Exception("Unknown media type %s" % mediatype)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/", 
                signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor="" and not Content-Location
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/",
                s.context)

    def test_parse_linkset_a2a_27(self):        
        PID = "https://w3id.org/a2a-fair-metrics/27-http-linkset-json-only//"
        for (uri,_) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri)
            self.assertEqual("https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/linkset.json", signposts.context_url)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/27-http-linkset-json-only/", signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor=""
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/27-http-linkset-json-only/", s.context)

    def test_parse_linkset_a2a_28(self):        
        PID = "https://w3id.org/a2a-fair-metrics/28-http-linkset-txt-only/"
        for (uri,_) in self._linksets_for_pid(PID):
            signposts = linkset.find_signposting_linkset(uri)
            self.assertEqual("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/linkset.txt", signposts.context_url)
            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/28-http-linkset-txt-only/", signposts.citeAs.target)

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/index.ttl"},
                {d.target for d in signposts.describedBy})
            self.assertEqual({"text/turtle"},
                {d.type for d in signposts.describedBy})

            self.assertEqual({"https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/test-apple-data.csv"},
                {i.target for i in signposts.items})
            self.assertEqual({"text/csv"},
                {i.type for i in signposts.items})

            self.assertEqual(3, len(signposts))
            # Assert context is picked up from anchor=""
            for s in signposts:
                self.assertEqual("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/", s.context)




# TODO: Check relative paths
# TODO: Check encoding of linkset file

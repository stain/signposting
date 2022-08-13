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

from signposting import linkset
from signposting.signpost import AbsoluteURI

a2a_27 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "27-http-linkset-json-only.json")
a2a_28 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "28-http-linkset-txt-only.txt")

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
        self.assertEqual("https://s11.no/2022/a2a-fair-metrics/28-http-linkset-txt-only/", signposts.citeAs.context)

        ## TODO: Test describedby and item

        self.assertEqual(3, len(signposts))


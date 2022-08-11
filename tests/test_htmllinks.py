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
"""Test htmllinks parsing."""

import unittest
import requests_mock
import importlib.resources

from signposting import htmllinks


a2a_02 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "02-html-full.html")
a2a_18 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "18-html-citeas-only.html")
a2a_19 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "19-html-citeas-multiple-rels.html")

class TestHtmlLinks(unittest.TestCase):
    def test_find_signposting_html(self):
        with requests_mock.Mocker() as m:
            m.get("https://w3id.example.org/a2a-fair-metrics/a02-html-full/", text=a2a_02)
            signposts = htmllinks.find_signposting_html("https://w3id.example.org/a2a-fair-metrics/a02-html-full/")            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/a02-html-full/", signposts.citeAs)


class TestDownloadedText(unittest.TestCase):
    pass

class TestGetHTML(unittest.TestCase):
    pass

class TestParseHTML(unittest.TestCase):
    pass

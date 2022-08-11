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
from urllib.error import HTTPError
import requests
import requests_mock
import importlib.resources

from signposting import htmllinks
from signposting.signpost import AbsoluteURI

a2a_02 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "02-html-full.html")
a2a_18 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "18-html-citeas-only.html")
a2a_19 = importlib.resources.read_text("tests.data.a2a-fair-metrics", "19-html-citeas-multiple-rels.html")

class TestHtmlLinks(unittest.TestCase):
    def test_find_signposting_html_a2a_18(self):
        with requests_mock.Mocker() as m:
            # This example.org URL will deliberaly only work through mocker
            URL="https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/"
            m.get(URL, 
                text=a2a_18, 
                headers={"Content-Type": "text/html;charset=UTF-8"})
            signposts = htmllinks.find_signposting_html(URL)            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/18-html-citeas-only/", signposts.citeAs.target)            # Note: Non-signposting links like rel=schema.DC are ignored
            self.assertEqual(1, len(signposts))

    def test_find_signposting_html_a2a_19(self):
        with requests_mock.Mocker() as m:
            URL="https://w3id.example.org/a2a-fair-metrics/19-html-citeas-multiple-rels/"
            m.get(URL, 
                text=a2a_19, 
                headers={"Content-Type": "text/html;charset=UTF-8"})
            signposts = htmllinks.find_signposting_html(URL)            
            self.assertEqual("https://w3id.org/a2a-fair-metrics/19-html-citeas-multiple-rels/", signposts.citeAs.target)            # Note: Non-signposting links like rel=schema.DC are ignored
            self.assertEqual(1, len(signposts))

    def test_find_signposting_html_a2a_02(self):
        with requests_mock.Mocker() as m:
            URL="https://w3id.example.org/a2a-fair-metrics/02-html-full/"
            m.get(URL, 
                text=a2a_02, 
                headers={"Content-Type": "text/html;charset=UTF-8"})
            signposts = htmllinks.find_signposting_html(URL)

            self.assertEqual("https://w3id.org/a2a-fair-metrics/02-html-full/", signposts.citeAs.target)
            self.assertEqual(
                {"https://orcid.org/0000-0002-1825-0097", "https://ror.org/02wg9xc72"},
                {a.target for a in signposts.authors}
            )
            self.assertEqual(
                {"https://schema.org/Dataset", "https://schema.org/AboutPage"},
                {t.target for t in signposts.types}
            )
            self.assertEqual(
                "https://creativecommons.org/licenses/by/4.0/",
                signposts.license.target
            )
            self.assertEqual(
                {"https://s11.no/2022/a2a-fair-metrics/02-html-full/data/test-apple-data.csv"},
                {i.target for i in signposts.items}
            )
            self.assertEqual(
                {"text/csv"},
                {i.type for i in signposts.items}
            )
            self.assertEqual(
                {"https://s11.no/2022/a2a-fair-metrics/02-html-full/metadata/02-html-full.jsonld", 
                "https://s11.no/2022/a2a-fair-metrics/02-html-full/metadata/02-html-full.xml"},
                {d.target for d in signposts.describedBy}
            )
            self.assertEqual(
                {"application/ld+json", "application/rdf+xml"},
                {d.type for d in signposts.describedBy}
            )
            # Note: Non-signposting links like rel=schema.DC are ignored
            self.assertEqual(9, len(signposts))

class TestDownloadedText(unittest.TestCase):
    def test_downloaded(self):
        d = htmllinks.DownloadedText("Hello World", "text/plain;charset=UTF-8",
            AbsoluteURI("http://example.com/"),
            AbsoluteURI("http://example.com/index.txt")
        )
        self.assertEqual("Hello World", d)
        self.assertEqual("text/plain;charset=UTF-8", d.content_type)
        self.assertEqual("http://example.com/", d.requested_url)
        self.assertEqual("http://example.com/index.txt", d.resolved_url)

    def test_html(self):
        html = htmllinks.HTML("<html><body>Hello</body></html>", 
            "text/html;charset=UTF-8",
            AbsoluteURI("http://example.com/"),
            AbsoluteURI("http://example.com/index.html")
        )
        self.assertEqual("<html><body>Hello</body></html>", html)

    def test_xhtml(self):
        xhtml = htmllinks.XHTML('<html xmlns="http://www.w3.org/1999/xhtml"><body>Hello</body></html>', 
            "application/xml+html",
            AbsoluteURI("http://example.com/"),
            AbsoluteURI("http://example.com/index.xhtml")
        )
        self.assertEqual('<html xmlns="http://www.w3.org/1999/xhtml"><body>Hello</body></html>', xhtml)

class TestUnrecognizedContentType(unittest.TestCase):
    def test_raise(self):
        with self.assertRaises(htmllinks.UnrecognizedContentType) as e:
            raise htmllinks.UnrecognizedContentType("image/jpeg", 
                AbsoluteURI("http://example.com/img1.jpeg"))
        self.assertEqual("image/jpeg", e.exception.content_type)
        self.assertEqual("http://example.com/img1.jpeg", e.exception.uri)

class TestGetHTML(unittest.TestCase):
    def test_get_html(self):
        with requests_mock.Mocker() as m:
            # This example.org URL will deliberaly only work through mocker
            URL=AbsoluteURI("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/")
            m.get(URL, 
                text=a2a_18, 
                headers={"Content-Type": "text/html;charset=UTF-8"})
            html = htmllinks._get_html(URL)            
            self.assertIn("<!doctype html>", html)
            self.assertIn("18-html-citeas-only", html)
            self.assertEqual("text/html;charset=UTF-8", html.content_type)
            self.assertEqual("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/", html.requested_url)
            self.assertEqual("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/", html.resolved_url)

    def test_get_html_resolved_relative(self):
        with requests_mock.Mocker() as m:
            # This example.org URL will deliberaly only work through mocker
            URL=AbsoluteURI("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/")
            m.get(URL, 
                text=a2a_18, 
                headers={"Content-Type": "text/html;charset=UTF-8",
                         "Content-Location": "index.html"})
            html = htmllinks._get_html(URL)            
            self.assertIn("<!doctype html>", html)
            self.assertIn("18-html-citeas-only", html)
            self.assertEqual("text/html;charset=UTF-8", html.content_type)
            self.assertEqual("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/", html.requested_url)
            self.assertEqual("https://w3id.example.org/a2a-fair-metrics/18-html-citeas-only/index.html", html.resolved_url)

    def test_get_html_404(self):
        with requests_mock.Mocker() as m:
            # This example.org URL will deliberaly only work through mocker
            URL=AbsoluteURI("https://w3id.example.org/a2a-fair-metrics/00-http-404-not-found/")
            m.get(URL, status_code=404)
            with self.assertRaises(requests.HTTPError):
                htmllinks._get_html(URL)

class TestParseHTML(unittest.TestCase):
    pass


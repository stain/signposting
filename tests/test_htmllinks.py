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
import importlib.resources

from signposting import htmllinks


a2a_02 = importlib.resources.path(".", "data/w3id.org/a2a-fair-metrics/02-html-full/index.html")
a2a_18 = importlib.resources.path(".", "data/w3id.org/a2a-fair-metrics/18-html-citeas-only/index.html")
a2a_19 = importlib.resources.path(".", "data/w3id.org/a2a-fair-metrics/19-html-citeas-multiple-rels/index.html")

class TestHtmlLinks(unittest.TestCase):
    def test_foo(self):
        self.assertEqual("http://example.com/author1", "Ouch")


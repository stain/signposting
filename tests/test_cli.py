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
"""Test the command line tool"""

import unittest
import os
from signposting import cli


class TestCommandLineToolParsing(unittest.TestCase):
    def test_bad_url(self):
        exit = cli.main("test://unknown-url-scheme")
        self.assertEqual(cli.errors.BAD_URL, exit)


@unittest.skipIf("CI" in os.environ, "Integration tests requires network access")
class TestCommandLineTool(unittest.TestCase):
    def test_00_404(self):
        exit = cli.main("https://w3id.org/a2a-fair-metrics/00-404-not-found/")
        self.assertEqual(cli.errors.BAD_URL, exit)

    def test_14_describedby(self):
        exit = cli.main(
            "https://w3id.org/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/")
        self.assertEqual(cli.errors.OK, exit)

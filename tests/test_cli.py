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
"""Test the command line tool"""

import unittest
import os
from signposting import cli
import sys
import warnings


class TestCommandLineToolParsing(unittest.TestCase):
    def test_bad_url(self):
        exit = cli.main("test://unknown-url-scheme")
        self.assertEqual(cli.ERROR.URL_ERROR, exit)
    def test_bad_url_sys_args(self):
        argv = sys.argv
        try:
            sys.argv = ["signposting", "test://unknown-url-scheme"]
            exit = cli.main()
            self.assertEqual(cli.ERROR.URL_ERROR, exit)
        finally:
            sys.argv = argv

@unittest.skipIf(os.environ.get("CI"), "Integration tests requires network access")
class TestCommandLineTool(unittest.TestCase):
    def test_00_404(self):
        exit = cli.main("https://w3id.org/a2a-fair-metrics/00-404-not-found/")
        self.assertEqual(cli.ERROR.HTTP_ERROR, exit)

    def test_14_describedby(self):
        exit = cli.main(
            "https://w3id.org/a2a-fair-metrics/14-http-describedby-citeas-linkset-json-txt-conneg/")
        self.assertEqual(cli.ERROR.OK, exit)

    def test_many(self):
        exit = cli.main("https://w3id.org/a2a-fair-metrics/01-http-describedby-only/", 
            "https://w3id.org/a2a-fair-metrics/02-html-full/", 
            "https://w3id.org/a2a-fair-metrics/03-http-citeas-only/")
        self.assertEqual(cli.ERROR.OK, exit)

    def test_25_410(self):
        with warnings.catch_warnings(record=True) as w:
            exit = cli.main("https://w3id.org/a2a-fair-metrics/25-http-citeas-author-410-gone/")
            self.assertEqual(cli.ERROR.OK, exit)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, UserWarning))
            self.assertIn("410 Gone", str(w[0].message))

    def test_29_500(self):
        exit = cli.main("https://w3id.org/a2a-fair-metrics/29-http-500-server-error/")
        self.assertEqual(cli.ERROR.HTTP_ERROR, exit)

    def test_23_many_signposts(self):
        exit = cli.main("https://w3id.org/a2a-fair-metrics/23-http-citeas-describedby-item-license-type-author/")
        self.assertEqual(cli.ERROR.OK, exit)

    def test_23_collection(self):
        exit = cli.main("https://s11.no/2022/a2a-fair-metrics/23-http-citeas-describedby-item-license-type-author/test-apple-data.csv")
        self.assertEqual(cli.ERROR.OK, exit)
    
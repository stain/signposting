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

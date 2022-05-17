"""Test Signpost classes"""

import unittest

from signposting.signpost import Signpost,AbsoluteURI,MediaType,LinkRel

class TestAbsoluteURI(unittest.TestCase):
    def testAbsoluteEqual(self):
        # Still a string!
        self.assertEqual("http://example.com/",
            AbsoluteURI("http://example.com/"))
    def testNotAbsolute(self):
        with self.assertRaises(ValueError):
            AbsoluteURI("/relative/path.html")
    def testNotValidURL(self):
        with self.assertRaises(ValueError):
            AbsoluteURI("http: // not valid")
            
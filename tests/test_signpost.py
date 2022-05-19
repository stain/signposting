"""Test Signpost classes"""

import unittest
import warnings

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
            self.assertEqual("https://www.iana.org/assignments/media-types/application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml",
                MediaType("https://www.iana.org/assignments/media-types/application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml"))
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
        self.assertEqual("example/92-#-z-$-x-&-^-_-+-.",
            MediaType("example/92-#-z-$-x-&-^-_-+-."))
        self.assertEqual("92-#-z-$-x-&-^-_-+-./example",
            MediaType("92-#-z-$-x-&-^-_-+-./example"))

        self.assertEqual("9/2",
            MediaType("9/2"))

    def testInvalidMain(self):
        with self.assertRaises(ValueError):
            MediaType(".example/wrong")
        with self.assertRaises(ValueError):
            MediaType("fantasy-$text/handwritten")
        with self.assertRaises(ValueError):
            MediaType(" text/plain")
        with self.assertRaises(ValueError):
            MediaType("*/*") # this is common in HTTP Accept!
        with self.assertRaises(ValueError):
            MediaType("image/*") 
        with self.assertRaises(ValueError):
            MediaType("-test/example") 
        with self.assertRaises(ValueError):
            MediaType("example/-test") 

    def testInvalidLength(self):
        x256 = "x" * 256
        x127 = "x" * 127
        
        # Maximum on either side
        MediaType("example/"+x127)
        MediaType(x127 + "/example")
        # This is the maximum permissable
        MediaType(x127+"/"+x127)

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

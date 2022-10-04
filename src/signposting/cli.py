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
"""
DOCSTRING for first public console interface.

USAGE:
    signposting
"""

from functools import reduce
# FIXME: Where can we import this from?
##from html.parser import HTMLParseError
from typing import Collection, Tuple
import argparse
import sys
import enum
from urllib.error import HTTPError, URLError
from signposting.htmllinks import UnrecognizedContentType, find_signposting_html
from signposting.linkset import LinksetParseError, find_signposting_linkset

from signposting.signpost import Signposting

from . import find_signposting_http, Signpost

def _multiline(header: str, lines: Collection[str]):
    """Format header, with subsequent lines indented correspondingly"""
    indent = "\n" + (" " * (len(header) + 2))
    return "%s: %s" % (header, indent.join(lines))


def _target(s: Signpost):
    """Format just target"""
    return "<%s>" % s.target


def _target_and_type(s: Signpost):
    """Format target and type"""
    return "<%s> %s" % (s.target,
                        s.type or "")

errors = enum.IntEnum("Error",
                      "OK URL_ERROR HTTP_ERROR LINK_SYNTAX INTERNAL_ERROR HTML_PARSE_ERROR UNRECOGNIZED_CONTENT_TYPE",
                      start=0
                      )
"""Error codes returned by CLI"""


def main(*args: str):
    """Discover signposting and print to STDOUT"""

    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs='+',
                        help="URL(s) to discover signposting for")
    parser.add_argument("--http", help="Find signposting in HTTP Link headers", 
        action='store_true')
    parser.add_argument("--html", help="Find signposting in <link> HTML elements if media-type matches", 
        action='store_true')
    parser.add_argument("--linkset", help="Find signposting in RFC9264 JSON or text linksets if media-type matches. When used with --recurse without specifying --http or --html, use those signposts to recurse, but only report from linksets",
        action='store_true')
    parser.add_argument("--all-linkset", help="Like --linkset, but parse both JSON and text variant if listed with same URI",
        action='store_true')
    parser.add_argument("-r", "--recurse", help="Follow and resolve rel=linkset signposts", 
        action='store_true'),
    parser.add_argument("-d", "--max-depth", help="Maximum depth of --recurse (default: 1)", 
        type=int, default=1)
    parser.add_argument("-m", "--merge", help="Merge reporting of signposting from multiple URLs, skipping any duplicate signposts. Forces --contexts",
        action='store_true'),
    parser.add_argument("-D", "--distinct", help="Report each signposting method (--http, --html and --linkset) separately",
        action='store_true'),
    parser.add_argument("-c", "--contexts", dest="contexts", help="Include signposts for other contexts/anchors than resolved URI", 
        action='store_true'),
    parser.add_argument("-f", "--format", help="Output format, plain text, HTTP link headers or RFC9264 JSON.", 
        choices="text link json".split(), default="text")

    if args:
        parsed = parser.parse_args(args)
    else:
        parsed = parser.parse_args()
    
    if not parsed.http and not parsed.html and not parsed.linkset:
        # No method specified, only HTTP/HTML by default
        parsed.http = True
        parsed.html = True
    
    isFirst = True
    signpostings: Tuple[str,Signposting] = []
    for url in parsed.url:
        if isFirst:
            isFirst = False
        else:
            print()  # separator

        if parsed.http:
            try:
                signposting = find_signposting_http(url)
                signpostings.append(("http", signposting))
            except HTTPError as e:
                print("HTTP error for %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.HTTP_ERROR
            except URLError as e:
                print("Failed URL %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.URL_ERROR
            except ValueError as e:
                print("Could not parse Link header for %s" % url, file=sys.stderr)
                print("%s" % e, file=sys.stderr)
                return errors.LINK_SYNTAX

        if parsed.html:
            try:
                signposting = find_signposting_html(url)
                signpostings.append(("html", signposting))
            except HTTPError as e:
                print("HTTP error for %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.HTTP_ERROR
            except IOError as e:
                print("Network error for %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.HTTP_ERROR
            except ValueError as e:
                print("Failed URL %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.URL_ERROR
#            except HTMLParseError as e:
#                print("Could not parse HTML for %s" % url, file=sys.stderr)
#                print("%s" % e, file=sys.stderr)
#                return errors.HTML_PARSE_ERROR
            except UnrecognizedContentType as e:
                if not parsed.http and not parsed.linkset:
                    # Silently ignore if other methods work
                    print("%s" % e, file=sys.stderr)
                    return errors.UNRECOGNIZED_CONTENT_TYPE
        
        if parsed.linkset:
            try:
                signposting = find_signposting_linkset(url)
                signpostings.append(("linkset", signposting))
            except HTTPError as e:
                print("HTTP error for %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.HTTP_ERROR
            except URLError as e:
                print("Failed URL %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.URL_ERROR
            except IOError as e:
                print("Network error for %s" % url, file=sys.stderr)
                print("%s" % e.reason, file=sys.stderr)
                return errors.HTTP_ERROR
            except LinksetParseError as e:
                print("Could not parse linkset for %s" % url, file=sys.stderr)
                print("%s" % e, file=sys.stderr)
                return errors.HTML_PARSE_ERROR
            except UnrecognizedContentType as e:
                print("%s" % e, file=sys.stderr)
                return errors.UNRECOGNIZED_CONTENT_TYPE

        if not parsed.distinct:
            signpostings = [("merged", 
                            reduce(lambda a,b: a|b, 
                                   (s for _,s in signpostings), 
                                   Signposting()))]
        for (method,signposting) in signpostings:
            print("Signposting for", signposting.context or url, 
                    " (%s)" % method if parsed.distinct else "")
            if (signposting.citeAs):
                print("CiteAs:", _target(signposting.citeAs))
            if (signposting.types):
                print(_multiline("Type", [_target(l) for l in signposting.types]))
            if (signposting.collection):
                print("Collection:", _target(signposting.collection))
            if (signposting.license):
                print("License:", _target(signposting.license))
            if (signposting.authors):
                print(_multiline("Author", [_target(l)
                    for l in signposting.authors]))
            if (signposting.describedBy):
                print(_multiline("DescribedBy", [
                    _target_and_type(l) for l in signposting.describedBy]))
            if (signposting.items):
                print(_multiline("Item", [_target_and_type(l)
                    for l in signposting.items]))
            if (signposting.linksets):
                print(_multiline("Linkset", [_target_and_type(l)
                    for l in signposting.linksets]))
    return errors.OK

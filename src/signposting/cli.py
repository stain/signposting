"""
DOCSTRING for first public console interface.

USAGE:
    signposting
"""

from typing import Dict, List, Set, Tuple, Optional, Collection, Set
import argparse
import sys
import enum
from urllib.error import HTTPError, URLError

from . import find_signposting, find_signposting_http, Signpost, Signposting

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
                      "OK URL_ERROR HTTP_ERROR LINK_SYNTAX INTERNAL_ERROR",
                      start=0
                      )
"""Error codes returned by CLI"""


def main(*args: str):
    """Discover signposting and print to STDOUT"""

    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs='+',
                        help="URL(s) to discover signposting for")
    if args:
        parsed = parser.parse_args(args)
    else:
        parsed = parser.parse_args()
    isFirst = True
    for url in parsed.url:
        if isFirst:
            isFirst = False
        else:
            print()  # separator

        try:
            signposting = find_signposting_http(url)
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
    #    except Exception as e:
    #        print("%s" % e, file=sys.stderr)
    #        return errors.INTERNAL_ERROR

        print("Signposting for", signposting.context_url or url)
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

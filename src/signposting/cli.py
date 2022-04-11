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

from . import Signposting,find_signposting,find_signposting_http,Link

def _multiline(header:str, lines:Collection[str]):
    indent = "\n" + (" " * (len(header)+2))
    return "%s: %s" % (header, indent.join(lines))

def _target(link: Link):
    return link.target

def _target_and_type(link: Link):
    return "%s %s" % (link.target, 
                      "type" in link and link["type"] or "")

errors = enum.IntEnum("Error", (
    "BAD_URL",
    "HTTP_ERROR",
    "LINK_SYNTAX",
    "INTERNAL_ERROR"
))

def main(*args:str):
    """Discover signposting"""
    
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args(args)
    try:
        signposting = find_signposting_http(args.url)
    except URLError as e:
        print("Failed URL %s" % args.url, file=sys.stderr)
        print("%s" % e.reason, file=sys.stderr)
        return errors.BAD_URL
    except HTTPError as e:
        print("HTTP error for %s" % args.url, file=sys.stderr)
        print("%s" % e.reason, file=sys.stderr)
        return errors.HTTP_ERROR
    except ValueError as e:
        print("Could not parse Link header for %s" % args.url, file=sys.stderr)
        print("%s" % e, file=sys.stderr)
        return errors.LINK_SYNTAX
#    except Exception as e:
#        print("%s" % e, file=sys.stderr)
#        return errors.INTERNAL_ERROR

    print("Signposting for", signposting.context_url or args.url)
    if (signposting.citeAs):            
        print("CiteAs:", _target(signposting.citeAs))
    if (signposting.type):
        print(_multiline("Type", map(_target, signposting.type)))
    if (signposting.collection):
        print("Collection:", _target(signposting.collection))
    if (signposting.license):
        print("License:", _target(signposting.license))
    if (signposting.author):
        print(_multiline("Author", map(_target, signposting.author)))
    if (signposting.describedBy):
        print(_multiline("DescribedBy", map(_target_and_type, signposting.describedBy)))
    if (signposting.item):
        print(_multiline("Item", map(_target_and_type, signposting.item)))
    if (signposting.linkset):
        print(_multiline("Linkset", map(_target_and_type, signposting.linkset)))

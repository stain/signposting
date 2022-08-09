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
Parse HTML to find <link> elements for signposting.
"""

import warnings
import requests
from bs4 import BeautifulSoup
from .signpost import SIGNPOSTING,Signpost,Signposting

def find_signposting(uri:str) -> Signposting:
    page = requests.get(uri)
    # TODO: Check return code
    context = page.url
    soup = BeautifulSoup(page.content, 'html.parser')
    signposts = []
    for link in soup.head.find_all("link"):
        # Ensure all filters are in lower case and known
        url = link.get("href")
        if not url:
            continue
        type = link.get("type")
        profile = link.get("profile", "")
        profiles = []
        if profile:
            profiles = profile.split(" ")
        rels = set(r.lower() for r in link.get("rel", [])
                    if r.lower() in SIGNPOSTING)
        for rel in rels:
            try:
                signpost = Signpost(rel, url, type, profiles, context)
            except ValueError as e:
                warnings.warn("Ignoring invalid signpost from %s: %s" % (uri, e))
                continue
            signposts.append(signpost)
    if not signposts:
        warnings.warn("No signposting found: %s" % uri)
    return Signposting(context, signposts)

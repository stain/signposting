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

import requests
from bs4 import BeautifulSoup
from httplink import ParsedLinks, Link
from .linkheader import Signposting
from .common import SIGNPOSTING

def find_signposting(uri:str) -> Signposting:
    page = requests.get(uri)
    soup = BeautifulSoup(page.content, 'html.parser')
    links = []
    for link in soup.head.find_all("link"):
        # Ensure all filters are in lower case and known
        rels = set(r.lower() for r in link.get("rel", []) if r.lower() in SIGNPOSTING)        
        if not rels:
            continue
        url = link.get("href")
        if not url:
            continue
        type = link.get("type")
        profile = link.get("profile")
        

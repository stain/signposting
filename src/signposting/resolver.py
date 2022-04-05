#   Copyright 2022 Stian Soiland-Reyes
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
Resolve a URI (possibly a PID) to find FAIR Signposting
"""

from urllib.request import Request, urlopen

from . import linkheader

def find_landing_page(url):
    req = Request(url, method="HEAD")
    link_headers = [] # Fall-back: No links
    with urlopen(req) as res:
        if (200 <= res.status < 300):
            # 200 OK or some other 2xx code
            link_headers = res.headers.get_all("Link")
            # TODO: Also check headers during redirection?
    
    # TODO: Also check HTML for <link>
    # TODO: Also check for linkset
    return linkheader.find_signposting(link_headers, res.geturl())
        
    
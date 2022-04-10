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

import urllib.request
import warnings
from . import linkheader


class _HTTPErrorHandler(urllib.request.HTTPDefaultErrorHandler):
    """A HTTP error handler that permits 410 Gone"""
    def http_error_410(self, req, fp, code, msg, headers):
        return fp
        

_http_opener = urllib.request.build_opener(_HTTPErrorHandler)
#urllib.request.install_opener(opener)

def find_signposting_http(url:str) -> linkheader.Signposting:
    """Find signposting from HTTP headers.

    Return a parsed `Signposting` object of the discovered signposting.
    """
    req = urllib.request.Request(url, method="HEAD")
    link_headers = [] # Fall-back: No links
    with _http_opener.open(req) as res:
        if (res.getcode() == 203):
            warnings.warn("203 Non-Authoritative Information <%s> - Signposting URIs may have been rewritten by proxy" % 
                res.geturl())
        elif (res.getcode() == 410):
            warnings.warn("410 Gone <%s> - still processing signposting for thumbstone page" % res.geturl())
            # Note: Other 4xx error codes would throw exceptions by _HTTPErrorHandler defaults
        link_headers = res.headers.get_all("Link")

    # TODO: Also check HTML for <link>
    # TODO: Also check for linkset
    return linkheader.find_signposting(link_headers, res.geturl())
        

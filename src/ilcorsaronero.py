# VERSION: 1.1
# AUTHORS: MarcelloCuoghi (https://github.com/MarcelloCuoghi)

# LICENSING INFORMATION
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from html.parser import HTMLParser
import time
from datetime import datetime

from helpers import download_file, retrieve_url
from novaprinter import prettyPrinter


class ilcorsaronero(object):
    url = "https://ilcorsaronero.link"
    name = "Il Corsaro Nero"
    supported_categories = {
        "all": "",
        "anime": "animazione",
        "boooks": "libri",
        "games": "giochi",
        "movies": "film",
        "music": "musica",
        "software": "software",
        "tv": "serie-tv",
    }

    class MyHtmlParser(HTMLParser):
        """Sub-class for parsing results"""

        A, TD, TR, HREF = ("a", "td", "tr", "href")

        def error(self, message):
            """Ignore errors"""
            pass

        def __init__(self, url):
            HTMLParser.__init__(self)
            self.url = url
            self.in_row = False
            self.in_link = False
            self.current_data = {}
            self.current_column = 0
            self.results = []
            self.capture_data = False

        def _get_magnet_link(self, href):
            """Extract magnet link from the page URL"""
            if not href:
                return None
            # Retrieve the page content
            html = retrieve_url(href)
            # Use regex to find the magnet link in the HTML content
            magnet_match = re.search(r'magnet:\?xt=urn:btih:[^"]+', html)
            if magnet_match:
                return magnet_match.group(0)
            return None

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "tr":
                self.in_row = True
                self.current_data = {}
                self.current_column = 0
            elif (
                self.in_row
                and tag == "a"
                and "href" in attrs
                and attrs["href"]
                and "/torrent/" in attrs["href"]
            ):
                self.in_link = True
                self.current_data["desc_link"] = f"{self.url}{attrs["href"]}"
            elif self.in_row and tag == "td":
                self.capture_data = True
            elif self.in_row and tag == "th":
                self.capture_data = True

        def handle_endtag(self, tag):
            if tag == "tr" and self.in_row:
                if "name" in self.current_data:
                    self.current_data["engine_url"] = self.url
                    self.current_data["link"] = self._get_magnet_link(
                        f"{self.current_data.get("desc_link", "")}"
                    )
                    prettyPrinter(self.current_data)
                    self.results.append(self.current_data)
                self.in_row = False
            elif tag == "a" and self.in_link:
                self.in_link = False
            elif tag in ("td", "th"):
                self.capture_data = False
                self.current_column += 1

        def handle_data(self, data):
            if self.in_row and self.capture_data:
                text = data.strip()
                if not text:
                    return
                if self.in_link:
                    self.current_data["name"] = text
                elif self.current_column == 2:
                    self.current_data["seeds"] = text
                elif self.current_column == 3:
                    self.current_data["leech"] = text
                elif self.current_column == 4:
                    self.current_data["size"] = text
                elif self.current_column == 5:
                    # Convert pub_date text to Unix timestamp
                    fmt = "%Y-%m-%d %H:%M"
                    try:
                        dt = datetime.strptime(text, fmt)
                        self.current_data["pub_date"] = int(time.mktime(dt.timetuple()))
                    except ValueError:
                        self.current_data["pub_date"] = text

    def download_torrent(self, info):
        print(download_file(info))

    # DO NOT CHANGE the name and parameters of this function
    # This function will be the one called by nova2.py
    def search(self, what, cat="all"):
        """Performs search"""
        parser = self.MyHtmlParser(self.url)
        what = what.replace("%20", "+")
        cat = self.supported_categories[cat]

        for page in range(1, 10):
            page_url = f"{self.url}/search?q={what}&page={page}&cat={cat}"
            html = retrieve_url(page_url)
            parser = self.MyHtmlParser(self.url)
            parser.feed(html)

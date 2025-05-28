# VERSION: 1.0
# AUTHORS: MarcelloCuoghi (https://github.com/MarcelloCuoghi)
# LICENSE: GPLv3

import re
from html.parser import HTMLParser

from helpers import retrieve_url, download_file
from novaprinter import prettyPrinter


class ilcorsaronero(object):
    url = "https://ilcorsaronero.link"
    name = "Il Corsaro Nero"
    supported_categories = {
        "all": "",
        "boooks": "libri",
        "anime": "animazione",
        "games": "giochi",
        "movies": "film",
        "music": "musica",
        "software": "software",
        "tv": "serie-tv",
        "other": "altro",
    }
    # IlCorsaroNero's search divided into pages, so we are going to set a limit on how many pages to read
    max_pages = 10

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
                self.current_data["desc_link"] = attrs["href"]
            elif self.in_row and tag == "td":
                self.capture_data = True
            elif self.in_row and tag == "th":
                self.capture_data = True

        def handle_endtag(self, tag):
            if tag == "tr" and self.in_row:
                if "name" in self.current_data:
                    self.current_data["engine_url"] = self.url
                    self.current_data["link"] = self._get_magnet_link(
                        f"{self.url}{self.current_data.get("desc_link", "")}"
                    )
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
                    self.current_data["pub_date"] = text
                # elif self.current_column == 6:
                #     self.current_data["uploader"] = text

    def download_torrent(self, info):
        print(download_file(info))

    # DO NOT CHANGE the name and parameters of this function
    # This function will be the one called by nova2.py
    def search(self, what, cat="all"):
        """Performs search"""
        parser = self.MyHtmlParser(self.url)
        what = what.replace("%20", "-")
        cat = self.supported_categories[cat]

        for page in range(1, 5):
            page_url = f"{self.url}/search?q={what}&page={page}&cat={cat}"
            html = retrieve_url(page_url)
            parser = self.MyHtmlParser(self.url)
            parser.feed(html)
            for torrent in parser.results:
                prettyPrinter(torrent)
            parser.close()

import abc
import itertools
import logging
import re
from abc import ABC
from typing import Any, Dict, Generator, List, Optional

import bs4
from bs4 import BeautifulSoup

from fuzzywuzzy import fuzz

from goodlibs.libgen import downloaders
from goodlibs.libgen.exceptions import CouldntFindDownloadUrl, NoResults
from goodlibs.libgen.publication import Publication

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, RetryError
from requests.packages.urllib3.util import Retry

RE_ISBN = re.compile(
    r"(ISBN[-]*(1[03])*[ ]*(: ){0,1})*" + r"(([0-9Xx][- ]*){13}|([0-9Xx][- ]*){10})"
)

RE_EDITION = re.compile(r"(\[[0-9] ed\.\])")


class Mirror(ABC):
    def __init__(self, search_url: str, book) -> None:
        self.search_url = search_url

        self.book = book
        self.search_term = str(book)
        self.logger = logging.getLogger(self.book.short_title)

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @staticmethod
    def get_href(cell) -> Optional[str]:
        links = cell.find_all("a", href=True)
        first = next(iter(links), None)
        return None if first is None else first.get("href")

    def search(self, start_at: int = 1) -> Generator[bs4.BeautifulSoup, None, None]:
        """
        Yield result pages for a given search term.

        :param start_at: results page to start at
        :returns: BeautifulSoup4 object representing a result page
        """
        if len(self.search_term) < 3:
            raise ValueError("Your search term must be at least 3 characters long.")

        self.logger.info(f'Searching for "{self.search_term}".')

        for page_url in self.next_page_url(start_at):
            r = self.session.get(page_url)
            if r.status_code == 200:
                publications = self.extract(BeautifulSoup(r.text, "html.parser"))

                if not publications:
                    raise NoResults
                else:
                    yield publications

    @abc.abstractmethod
    def next_page_url(self, start_at: int) -> Generator[str, None, None]:
        """Yields the new results page."""
        raise NotImplementedError

    @abc.abstractmethod
    def extract(self, page) -> List[Publication]:
        """Extract all the results info in a given result page.

        :param page: result page as an BeautifulSoup4 object
        :returns: list of :class:`Publication` objects
        """
        raise NotImplementedError

    def get_results(self):
        results = []
        try:
            for publications in self.search():
                results.extend(publications)
        except NoResults:
            pass
        return results

    def select_result(self, results, language, extensions):
        # Filter out results that do not match the language and extension preferences.
        filtered_results = filter(
            lambda result: result.lang == language and result.extension in extensions, results
        )

        def result_key(result):
            extension_rank = extensions.index(result.extension)
            title_difference = 100 - fuzz.ratio(self.book.title, result.title)
            return title_difference, extension_rank

        # Sort the results by order of most similar title and preferred file format.
        sorted_results = sorted(filtered_results, key=result_key)

        # Return the result matching the preferences, if any.
        try:
            return sorted_results[0]
        except IndexError:
            return None

    # TODO: make it do parallel multipart download
    # http://stackoverflow.com/questions/1798879/download-file-using-partial-download-http
    def download(self, publication):
        """
        Download a publication from the mirror to the current directory.

        :param publication: a Publication
        """
        for (n, mirror) in publication.mirrors.items():
            try:
                mirror.download_publication(self.session, publication)
                break  # stop if successful
            except CouldntFindDownloadUrl as e:
                self.logger.warning(f"{e} Trying a different mirror.")
            except (RetryError, ConnectionError):
                self.logger.warning("Max retries exceeded. Trying a different mirror.")
                continue
            except Exception as e:
                self.logger.error(f"{e} Failed to download.")
                continue


class GenLibRusEc(Mirror):
    search_url = "http://gen.lib.rus.ec/search.php?req="

    def __init__(self, book) -> None:
        super().__init__(self.search_url, book)

    def next_page_url(self, start_at: int) -> Generator[str, None, None]:
        """Yields the new results page."""
        for pn in itertools.count(start_at):
            yield f"{self.search_url}{self.search_term}&page={str(pn)}"

    def extract(self, page):
        """Extract all the publications info in a given result page.

        :param page: result page as an BeautifulSoup4 object
        :returns: list of Publication
        """
        rows = page.find_all("table")[2].find_all("tr")
        results = []
        for row in rows[1:]:
            cells = row.find_all("td")
            attrs = self.extract_attributes(cells)
            results.append(Publication(attrs))
        return results

    def extract_attributes(self, cells) -> Dict[str, Any]:
        attrs = {}
        attrs["id"] = cells[0].text
        attrs["authors"] = cells[1].text.strip()

        # The 2nd cell contains title information
        # In best case it will have: Series - Title - Edition - ISBN
        # But everything except the title is optional
        # and this optional text shows up in green font
        for el in cells[2].find_all("font"):
            et = el.text
            if RE_ISBN.search(et) is not None:
                # A list of ISBNs
                attrs["isbn"] = [
                    RE_ISBN.search(n).group(0)
                    for n in et.split(",")
                    if RE_ISBN.search(n) is not None
                ]
            elif RE_EDITION.search(et) is not None:
                attrs["edition"] = et
            else:
                attrs["series"] = et

            # Remove this element from the DOM
            # so that it isn't considered a part of the title
            el.extract()

        # Worst case: just fill everything in the title field
        attrs["title"] = cells[2].text.strip()

        attrs["publisher"] = cells[3].text
        attrs["year"] = cells[4].text
        attrs["pages"] = cells[5].text
        attrs["lang"] = cells[6].text
        attrs["size"] = cells[7].text
        attrs["extension"] = cells[8].text

        libgen_is_url = Mirror.get_href(cells[9])
        libgen_lc_url = Mirror.get_href(cells[10])
        b_ok_cc_url = Mirror.get_href(cells[11])

        attrs["mirrors"] = {
            "libgen.is": downloaders.LibgenIsDownloader(libgen_is_url, self.logger),
            "libgen.lc": downloaders.LibgenLcDownloader(libgen_lc_url, self.logger),
            "b-ok.cc": downloaders.BOkCcDownloader(b_ok_cc_url, self.logger),
        }
        return attrs


class LibGenIs(GenLibRusEc):
    search_url = "https://libgen.is/search.php?req="


MIRRORS = {"http://gen.lib.rus.ec": GenLibRusEc, "https://libgen.is": LibGenIs}


def find_mirror(book):
    for homepage, mirror in MIRRORS.items():
        homepage_response = requests.get(homepage)
        if homepage_response.status_code == 200:
            return mirror(book=book)
    return None

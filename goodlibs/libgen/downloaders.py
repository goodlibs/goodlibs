import abc
import logging
import os.path
import platform
from abc import ABC
from threading import Thread
from typing import Optional

from bs4 import BeautifulSoup

from goodlibs.libgen import mirrors
from goodlibs.libgen.exceptions import CouldntFindDownloadUrl
from goodlibs.libgen.utils import random_string

import requests


class MirrorDownloader(ABC):
    def __init__(self, url: str, logger: logging.Logger, timeout: int = 10) -> None:
        """Constructs a new MirrorDownloader.

        :param url: URL from where to try to download file
        :param timeout: number of seconds for the download request to timeout
        :rtype: None
        """
        self.url = url
        self.timeout = timeout  # in seconds
        self.logger = logger

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.url}>"

    def download_publication(self, session, publication):
        """Downloads a publication from 'self.url'."""
        r = session.get(self.url, timeout=self.timeout, stream=False)
        html = BeautifulSoup(r.text, "html.parser")
        download_url = self.get_download_url(html)
        if download_url is None:
            raise CouldntFindDownloadUrl(self.url)
        filename = publication.filename()
        self.logger.info(f'Downloading "{filename}".')
        data = session.get(download_url, timeout=self.timeout, stream=True)
        self.save_file(filename, data)

    def save_file(self, filename: str, data: requests.models.Response):
        """Saves a file to the current directory."""

        def filter_filename(filename: str):
            """Filters a filename non alphabetic and non delimiters charaters."""
            valid_chars = "-_.() "
            return "".join(c for c in filename if c.isalnum() or c in valid_chars)

        filename = filter_filename(filename)
        try:
            with open(filename, "wb") as f:
                for chunk in data.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            self.logger.info(f'Saved file as "{filename}".')
        except OSError as exc:
            if (platform.system() == "Linux" and exc.errno == 36) or (
                platform.system() == "Darwin" and exc.errno == 63
            ):  # filename too long
                (_, extension) = os.path.splitext(filename)  # this can fail
                # 'extension' already contains the leading '.', hence
                # there is no need for a '.' in between "{}{}"
                random_filename = f"{random_string(15)}{extension}"
                self.save_file(random_filename, data)
            else:
                raise  # re-raise if .errno is different than 36 or 63
        except Exception:
            raise

    @abc.abstractmethod
    def get_download_url(self, html) -> Optional[str]:
        """Returns the URL from where to download the
        file or None if it can't find the URL."""
        raise NotImplementedError


class LibgenIsDownloader(MirrorDownloader):
    """MirrorDownloader for 'libgen.is'."""

    def __init__(self, url: str, logger: logging.Logger) -> None:
        super().__init__(url, logger)

    def get_download_url(self, html) -> Optional[str]:
        a = html.find("a", href=True, text="GET")
        return None if a is None else a.get("href")


class LibgenLcDownloader(LibgenIsDownloader):
    pass


class BOkCcDownloader(MirrorDownloader):
    """MirrorDownloader for 'b-ok.cc'."""

    def __init__(self, url: str, logger: logging.Logger) -> None:
        super().__init__(url, logger)

    def get_download_url(self, html) -> Optional[str]:
        # a = html.find('a', class_='ddownload', href=True)
        # return None if a is None else a.get('href')
        raise Exception("The b-ok.cc MirrorDownloader is broken.")


def download_books(books, language="English", extensions=("mobi", "epub", "pdf")):
    for book in books:
        # Configure logger.
        logger = logging.getLogger(book.short_title)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s (%(name)s): %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        mirror = mirrors.find_mirror(book)
        if mirror is None:
            logger.error("Unable to find an active mirror. Skipping.")
            continue
        results = mirror.get_results()
        selected = mirror.select_result(results, language, extensions)
        if selected:
            logger.info("Found book.")
            downloader = Thread(target=mirror.download, args=[selected])
            downloader.start()
        else:
            logger.info("No results found for the specified language and extensions.")
            pass

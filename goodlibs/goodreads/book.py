import logging
import re

from betterreads import client

from unidecode import unidecode


class Book:
    def __init__(self, book_dict):
        self._book_dict = book_dict

    def __repr__(self):
        """String representation used for queries."""
        author = unidecode(self.author or "").lower()  # Transliterate and lowercase.
        author_words = re.split("[\W\s]", author)  # noqa = W605  # Remove punctuation.
        author_words = [
            word for word in author_words if len(word) > 1 and word not in ("jr", "sr", "ii", "iii")
        ]  # Remove initials and suffixes.

        title = unidecode(
            self.short_title
        ).lower()  # Remove subtitles, transliterate, and lowercase.
        title_words = re.split("[\W\s]", title)  # noqa = W605  # Remove punctuation.

        words = [word.strip() for word in author_words + title_words]  # Strip spaces.
        return " ".join(words)  # Lower case.

    @property
    def title(self):
        """Returns the title of the book (without the series)."""
        return self._book_dict["title_without_series"]

    @property
    def short_title(self):
        """Returns the shortened title of the book (without the subtitle)."""
        return self.title.split(":")[0]

    @property
    def author(self):
        """Returns the first author name if it is known."""
        # Get the first author name from the list.
        author_dicts = self._book_dict["authors"]["author"]
        if type(author_dicts) == list:
            author_name = author_dicts[0]["name"]
        else:
            author_name = author_dicts["name"]
        # If the author is not known, return None.
        if author_name.lower() in {"anonymous", "unknown"}:
            return None
        return author_name


def get_books(api_key, username, shelf_name="to-read"):
    # Configure logger.
    logger = logging.getLogger("Goodreads")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s (%(name)s): %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Initialize Goodreads client and user.
    logger.info("Authenticating with the Goodreads API.")
    goodreads_client = client.GoodreadsClient(client_key=api_key, client_secret=None)
    user = goodreads_client.user(username=username)

    # Get books from the specified shelf.
    logger.info(f'Getting the list of books from {username}\'s "{shelf_name}" shelf.')
    reviews = user.per_shelf_reviews(shelf_name=shelf_name)

    # Normalize the list of books.
    books = [Book(book_dict=review.book) for review in reviews]

    return books

# goodlibs

[![build](https://github.com/goodlibs/goodlibs/workflows/build/badge.svg)](https://github.com/goodlibs/goodlibs/actions?query=workflow%3Abuild) [![Latest Version](https://img.shields.io/pypi/v/goodlibs.svg)](https://pypi.python.org/pypi/goodlibs) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/goodlibs.svg)](https://pypi.python.org/pypi/goodlibs) [![Code Style: Black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/python/black)

Download books from a Goodreads shelf using Library Genesis.

## :books: Background

[Goodreads](https://www.goodreads.com/) is a social cataloging website that allows you to search for books and save them to reading lists, known as "shelves".

[Library Genesis](https://libgen.is/) (Libgen) is a file-sharing website for scholarly journal articles, academic and general-interest books, images, comics, and magazines.

**goodlibs** is a simple utility that searches for and downloads all items from a Goodreads shelf using Libgen.
It was built using [`betterreads`](https://github.com/thejessleigh/betterreads) and a modified fork of [`libgen.py`](https://github.com/adolfosilva/libgen.py).

_[In solidarity with Library Genesis](http://custodians.online/). In memory of Aaron Swartz._

## :hammer_and_wrench: Installation

Install using [pip](https://pip.pypa.io/en/stable/quickstart/):

```bash
pip3 install goodlibs
```

### Goodreads setup

1. Register for a [Goodreads API key](https://www.goodreads.com/api/keys) in order to access your list of books.
2. Ensure your [Goodreads account privacy settings](https://www.goodreads.com/user/edit?tab=settings) allow for access to your shelves via the API.
    - Set `Who can view my profile:` to `anyone (including search engines)`
    - Check the box `Allow partners of Goodreads to display my reviews`

## :computer: Usage

### :heavy_dollar_sign: From the command line

For basic usage, start with the `download` command:

```bash
goodlibs download --help
```

If you want to save your options for later, use the `configure` command:

```bash
goodlibs configure --help
```

Typical usage:

```bash
goodlibs download -k yourgoodreadsapikey -u yourgoodreadsusername -e mobi -e epub -e pdf
```

### :page_with_curl: From a script

```python
from goodlibs import goodreads, libgen

# Get the list of books from Goodreads.
books = goodreads.get_books(api_key="yourgoodreadsapikey",
                            username="yourgoodreadsusername",
                            shelf_name="to-read")              # Optional.

# Query Libgen with the list of books.
libgen.download_books(books=books,
                      language="English",                      # Optional.
                      extensions=("mobi", "epub", "pdf"))      # Optional.
```

## :balance_scale: License

This code is licensed under the GNU General Public License v3.0.
For more details, please take a look at the [LICENSE](https://github.com/goodlibs/goodlibs/blob/master/LICENSE) file.

## :handshake: Contributing

Contributions are welcome!
Please feel free to open an issue or submit a pull request.

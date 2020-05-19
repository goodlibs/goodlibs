import os
from configparser import ConfigParser
from pathlib import Path

import click

from goodlibs import goodreads, libgen


def config_file(touch=False):
    config_path = Path("~/.goodlibs/config")
    expanded_config_path = config_path.expanduser()

    if not expanded_config_path.exists() and touch:
        os.makedirs(expanded_config_path.parent)
        expanded_config_path.touch()

    return expanded_config_path


@click.group()
def cli():
    """Download books from a Goodreads shelf using Library Genesis."""
    pass


@cli.command()
@click.option("--key", "-k", help="Goodreads API key.")
@click.option("--username", "-u", help="Username of the Goodreads user.")
@click.option("--shelf", "-s", help="Name of the Goodreads shelf.")
@click.option("--language", "-l", help="Language of the eBooks to download.")
@click.option(
    "--extension",
    "-e",
    multiple=True,
    help="Format of the eBooks to download, in order of preference.",
)
def configure(key, username, shelf, language, extension):
    """Configure Goodreads secrets and Libgen download preferences.

    Configurations are stored in "~/.goodlibs/config".
    """
    config = ConfigParser()
    config.read(config_file(touch=True))

    if "Goodreads" not in config:
        config["Goodreads"] = {}
    config["Goodreads"]["api_key"] = key or config["Goodreads"].get("api_key")
    config["Goodreads"]["username"] = username or config["Goodreads"].get("username")
    config["Goodreads"]["shelf"] = shelf or config["Goodreads"].get("shelf")

    if "Library Genesis" not in config:
        config["Library Genesis"] = {}
    config["Library Genesis"]["language"] = language or config["Library Genesis"].get("language")
    config["Library Genesis"]["extensions"] = (
        None if extension == () else ", ".join(extension)
    ) or config["Library Genesis"].get("extensions")

    config.write(config_file().open("w"))


@cli.command()
@click.option("--key", "-k", help="Goodreads API key.")
@click.option("--username", "-u", help="Username of the Goodreads user.")
@click.option("--shelf", "-s", help="Name of the Goodreads shelf.")
@click.option("--language", "-l", help="Language of the eBooks to download.")
@click.option(
    "--extension",
    "-e",
    multiple=True,
    help="Format of the eBooks to download, in order of preference.",
)
def download(key, username, shelf, language, extension):
    """Download books from Libgen."""
    # Read config file.
    config = ConfigParser()
    config.read(config_file())

    def deep_get(dictionary, key_1, key_2):
        if key_1 not in dictionary:
            return None
        else:
            return dictionary[key_1].get(key_2)

    # Validate options and fall back to stored configurations or defaults.
    if key is None:
        if deep_get(config, "Goodreads", "api_key") is not None:
            key = config["Goodreads"]["api_key"]
        else:
            click.echo(
                message="The Goodreads API key is required. "
                "Register for an API key here: https://www.goodreads.com/api/keys",
                err=True,
            )
            key = click.prompt(text="key")

    if username is None:
        if deep_get(config, "Goodreads", "username") is not None:
            username = config["Goodreads"]["username"]
        else:
            click.echo(message="The Goodreads username is required.", err=True)
            username = click.prompt(text="username")

    if shelf is None:
        if deep_get(config, "Library Genesis", "shelf") is not None:
            shelf = config["Library Genesis"]["shelf"]
        else:
            shelf = "to-read"

    if language is None:
        if deep_get(config, "Library Genesis", "language") is not None:
            language = config["Library Genesis"]["language"]
        else:
            language = "English"

    if extension == ():
        if deep_get(config, "Library Genesis", "extensions") is not None:
            extension = tuple(config["Library Genesis"]["extensions"].split(", "))
        else:
            extension = ("mobi", "epub", "pdf")

    # Get the list of books from Goodreads.
    books = goodreads.get_books(api_key=key, username=username, shelf_name=shelf)

    # Query Libgen with the list of books.
    libgen.download_books(books=books, language=language, extensions=extension)

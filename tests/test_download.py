import pickle

import pytest


@pytest.fixture()
def books():
    with open("tests/data/books.pickle", "rb") as f:
        return pickle.load(f)

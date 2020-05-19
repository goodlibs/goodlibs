from setuptools import find_packages, setup

required_packages = [
    "beautifulsoup4",
    "betterreads",
    "click",
    "fuzzywuzzy",
    "requests",
    "python-Levenshtein",
    "Unidecode",
]

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="goodlibs",
    version="0.1.1",
    description="Download books from a Goodreads shelf using Library Genesis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/goodlibs/goodlibs",
    author="goodlibs",
    author_email="hello@goodlibs.com",
    classifiers=(
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
    ),
    packages=find_packages(),
    include_package_data=True,
    install_requires=required_packages,
    entry_points={"console_scripts": ["goodlibs=goodlibs.cli:cli"]},
)

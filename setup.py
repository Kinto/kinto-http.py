import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    """Open a related file and return its content."""
    with codecs.open(os.path.join(here, filename), encoding="utf-8") as f:
        content = f.read()
    return content


README = read_file("README.rst")
CHANGELOG = read_file("CHANGELOG.rst")

INSTALL_REQUIRES = [
    x.replace(" \\", "")
    for x in read_file("./requirements.txt").split("\n")
    if not x.startswith(" ")
]

TESTS_REQUIRE = [
    x.replace(" \\", "")
    for x in read_file("./dev-requirements.txt").split("\n")
    if not x.startswith(" ")
]

setup(
    name="kinto-http",
    version="10.10.0",
    description="Kinto client",
    long_description=README + "\n\n" + CHANGELOG,
    license="Apache License (2.0)",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords="web services",
    author="Mozilla Services",
    author_email="storage@mozilla.com",
    url="https://github.com/Kinto/kinto-http.py/",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    test_suite="kinto_http.tests",
    tests_require=TESTS_REQUIRE,
)

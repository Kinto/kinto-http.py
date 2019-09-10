import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    README = f.read()

REQUIREMENTS = ["requests>=2.8.1", "unidecode"]

test_requirements = [
    "pytest",
    "pytest-cache",
    "pytest-cov",
    "pytest-sugar",
    "pytest-xdist",
    "kinto",
    "unidecode",
]

setup(
    name="kinto-http",
    version='10.5.0',
    description="Kinto client",
    long_description=README,
    license="Apache License (2.0)",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
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
    install_requires=REQUIREMENTS,
    test_suite="kinto_http.tests",
    tests_require=test_requirements,
)

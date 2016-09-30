import codecs
import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    README = f.read()

REQUIREMENTS = [
    'requests>=2.8.1',
    'unidecode',
    'six'
]


if sys.version_info < (2, 7, 9):
    # For secure SSL connexion with Python 2.7 (InsecurePlatformWarning)
    REQUIREMENTS.append('PyOpenSSL')
    REQUIREMENTS.append('ndg-httpsclient')
    REQUIREMENTS.append('pyasn1')

test_requirements = [
    'pytest',
    'pytest-cache',
    'pytest-cover',
    'pytest-sugar',
    'pytest-xdist',
    'mock',
    'kinto',
    'unittest2',
    'unidecode',
    'six',
]

setup(name='kinto-http',
      version='7.1.0.dev0',
      description='Kinto client',
      long_description=README,
      license='Apache License (2.0)',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          "License :: OSI Approved :: Apache Software License"
      ],
      keywords="web services",
      author='Mozilla Services',
      author_email='storage@mozilla.com',
      url='https://github.com/Kinto/kinto-http.py/',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      test_suite='kinto_http.tests',
      tests_require=test_requirements)

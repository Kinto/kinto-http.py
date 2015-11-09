import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    README = f.read()

REQUIREMENTS = [
    'PyFxA',
    'requests',
    'requests-hawk',
    'unidecode',
    'six'
]

setup(name='kinto-client',
      version='1.0.1.dev0',
      description='Kinto client',
      long_description=README,
      license='Apache License (2.0)',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          "License :: OSI Approved :: Apache Software License"
      ],
      keywords="web services",
      author='Mozilla Services',
      author_email='storage@mozilla.com',
      url='https://kintoclient.readthedocs.org',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS)

Kinto python client
###################

.. image:: https://img.shields.io/travis/Kinto/kinto-http.py.svg
        :target: https://travis-ci.org/Kinto/kinto-http.py

.. image:: https://img.shields.io/pypi/v/kinto-http.svg
        :target: https://pypi.python.org/pypi/kinto-http

.. image:: https://coveralls.io/repos/Kinto/kinto-http.py/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-http.py


*kinto-http* is the Python library to interact with a *Kinto* server.

There is also a similar `client in JavaScript <https://github.com/kinto/kinto-http.js>`_.


Installation
============

Use pip::

  $ pip install kinto-http


Usage
=====

Here is an overview of what the API provides:

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(server_url="http://localhost:8888/v1",
                               auth=('alexis', 'p4ssw0rd'))

    records = client.get_records(bucket='default', collection='todos')
    for i, record in enumerate(records):
        record['title'] = 'Todo {}'.format(i)
        client.update_record(data=record)


Instantiating a client
----------------------

The passed ``auth`` parameter is a `requests <http://docs.python-requests.org>`_
authentication policy.

By default, a simple tuple will become a ``Basic Auth`` authorization request header, that can authenticate users with `Kinto Accounts <https://kinto.readthedocs.io/en/stable/api/1.x/accounts.html>`_.

.. code-block:: python

    import kinto_http

    auth = ('alexis', 'p4ssw0rd')

    client = kinto_http.Client(server_url='http://localhost:8888/v1',
                               auth=auth)

It is also possible to pass a ``bucket`` ID and/or ``collection`` ID to set them as default values for the parameters of the client operations.

.. code-block:: python

    client = Client(bucket="payments", collection="receipts", auth=auth)

After creating a client, you can also replicate an existing one and overwrite
some key arguments.

.. code-block:: python

    client2 = client.clone(collection="orders")


Using a Bearer access token to authenticate (OpenID)
----------------------------------------------------

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(auth=kinto_http.BearerTokenAuth("XYPJTNsFKV2"))


The authorization header is prefixed with ``Bearer`` by default. If the ``header_type``
is `customized on the server <https://kinto.readthedocs.io/en/stable/configuration/settings.html#openid-connect>`_,
the client must specify the expected type: ``kinto_http.BearerTokenAuth("XYPJTNsFKV2" type="Bearer+OIDC")``


Getting server information
--------------------------

You can use the ``server_info()`` method to fetch the server information:

.. code-block:: python

    from kinto_http import Client

    client = Client(server_url='http://localhost:8888/v1')
    info = client.server_info()
    assert 'schema' in info['capabilities'], "Server doesn't support schema validation."


Bucket operations
-----------------

* ``get_bucket(id=None, **kwargs)``: retrieve single bucket
* ``get_buckets(**kwargs)``: retrieve all readable buckets
* ``create_bucket(id=None, data=None, **kwargs)``: create a bucket
* ``update_bucket(id=None, data=None, **kwargs)``: create or replace an existing bucket
* ``patch_bucket(id=None, changes=None, **kwargs)``: modify some fields in an existing bucket
* ``delete_bucket(id=None, **kwargs)``: delete a bucket and everything under it
* ``delete_buckets(**kwargs)``: delete every writable buckets


Groups operations
-----------------

* ``get_group(id=None, bucket=None, **kwargs)``: retrieve single group
* ``get_groups(bucket=None, **kwargs)``: retrieve all readable groups
* ``create_group(id=None, data=None, bucket=None, **kwargs)``: create a group
* ``update_group(id=None, data=None, bucket=None, **kwargs)``: create or replace an existing group
* ``patch_group(id=None, changes=None, bucket=None, **kwargs)``: modify some fields in an existing group
* ``delete_group(id=None, bucket=None, **kwargs)``: delete a group and everything under it
* ``delete_groups(bucket=None, **kwargs)``: delete every writable groups


Collections
-----------

* ``get_collection(id=None, bucket=None, **kwargs)``: retrieve single collection
* ``get_collections(bucket=None, **kwargs)``: retrieve all readable collections
* ``create_collection(id=None, data=None, bucket=None, **kwargs)``: create a collection
* ``update_collection(id=None, data=None, bucket=None, **kwargs)``: create or replace an existing collection
* ``patch_collection(id=None, changes=None, bucket=None, **kwargs)``: modify some fields in an existing collection
* ``delete_collection(id=None, bucket=None, **kwargs)``: delete a collection and everything under it
* ``delete_collections(bucket=None, **kwargs)``: delete every writable collections


Records
-------

* ``get_record(id=None, bucket=None, collection=None, **kwargs)``: retrieve single record
* ``get_records(bucket=None, collection=None, **kwargs)``: retrieve all readable records
* ``get_paginated_records(bucket=None, collection=None, **kwargs)``: paginated list of records
* ``get_records_timestamp(bucket=None, collection=None, **kwargs)``: return the records timestamp of this collection
* ``create_record(id=None, data=None, bucket=None, collection=None, **kwargs)``: create a record
* ``update_record(id=None, data=None, bucket=None, collection=None, **kwargs)``: create or replace an existing record
* ``patch_record(id=None, changes=None, bucket=None, collection=None, **kwargs)``: modify some fields in an existing record
* ``delete_record(id=None, bucket=None, collection=None, **kwargs)``: delete a record and everything under it
* ``delete_records(bucket=None, collection=None, **kwargs)``: delete every writable records


Permissions
-----------

The objects permissions can be specified or modified by passing a ``permissions`` to ``create_*()``, ``patch_*()``, or ``update_*()`` methods:

.. code-block:: python

    client.create_record(data={'foo': 'bar'},
                         permissions={'read': ['group:groupid']})


    record = client.get_record('123', collection='todos', bucket='alexis')
    record['permissions']['write'].append('leplatrem')
    client.update_record(data=record)


Get or create
-------------

In some cases, you might want to create a bucket, collection, group or record only if
it doesn't exist already. To do so, you can pass the ``if_not_exists=True``
to the ``create_*()`` methods::

  client.create_bucket(id='blog', if_not_exists=True)
  client.create_collection(id='articles', bucket='blog', if_not_exists=True)


Delete if exists
----------------

In some cases, you might want to delete a bucket, collection, group or record only if
it exists already. To do so, you can pass the ``if_exists=True``
to the ``delete_*`` methods::

  client.delete_bucket(id='bucket', if_exists=True)


Patch operations
----------------

The ``.patch_*()`` operations receive a ``changes`` parameter.


.. code-block:: python

    from kinto_http.patch_type import BasicPatch, MergePatch, JSONPatch


    client.patch_record(id='abc', changes=BasicPatch({'over': 'write'}))

    client.patch_record(id='todo', changes=MergePatch({'assignee': 'bob'}))

    client.patch_record(id='receipts', changes=JSONPatch([
        {'op': 'add', 'path': '/data/members/0', 'value': 'ldap:user@corp.com'}
    ]))


Concurrency control
-------------------

The ``create_*()``, ``patch_*()``, and ``update_*()`` methods take a ``safe`` argument (default: ``True``).

If ``True``, the client will ensure that the object wasn't modified on the server side since we fetched it. The timestamp will be implicitly read from the ``last_modified`` field in the passed ``data`` object, or taken explicitly from the ``if_match`` parameter.


Batching operations
-------------------

Rather than issuing a request for each and every operation, it is possible to
batch several operations in one request.

Using the ``batch()`` method as a Python context manager (``with``):

.. code-block:: python

  with client.batch() as batch:
      for idx in range(0, 100):
          batch.update_record(data={'id': idx})

.. note::

    Besides the ``results()`` method, a batch object shares all the same methods as
    another client.

Reading data from batch operations is achieved by using the ``results()`` method
available after a batch context is closed.

.. code-block:: python

  with client.batch() as batch:
      batch.get_record('r1')
      batch.get_record('r2')
      batch.get_record('r3')

  r1, r2, r3 = batch.results()


Errors
------

Failing operations will raise a ``KintoException``, which has ``request`` and ``response`` attributes.

.. code-block:: python

    try:
        client.create_group(id="friends")
    except kinto_http.KintoException as e:
        if e.response and e.response.status_code == 403:
            print("Not allowed!")


Retry on error
--------------

When the server is throttled (under heavy load or maintenance) it can
return error responses.

The client can hence retry to send the same request until it succeeds.
To enable this, specify the number of retries on the client:

.. code-block:: python

  client = Client(server_url='http://localhost:8888/v1',
                  auth=credentials,
                  retry=10)

The Kinto protocol lets the server `define the duration in seconds between retries
<https://kinto.readthedocs.io/en/latest/api/1.x/backoff.html>`_.
It is possible (but not recommended) to force this value in the clients:

.. code-block:: python

  client = Client(server_url='http://localhost:8888/v1',
                  auth=credentials,
                  retry=10,
                  retry_after=5)

Pagination
----------

When the server responses are paginated, the client will download every page and
merge them transparently.

The ``get_paginated_records()`` method returns a generator that will yield each page:


.. code-block:: python

  for page in client.get_paginated_records():
      records = page["data"]

It is possible to specify a limit for the number of items to be retrieved in one page:

.. code-block:: python

    records = client.get_records(_limit=10)

In order to retrieve every available pages with a limited number of items in each
of them, you can specify the number of pages:

.. code-block:: python

    records = client.get_records(_limit=10, pages=float('inf'))  # Infinity


Endpoint URLs
-------------

The ``get_endpoint()`` method returns an endpoint URL on the server:

.. code-block:: python

    client = Client(server_url='http://localhost:8888/v1',
                    auth=('token', 'your-token'),
                    bucket="payments",
                    collection="receipts")

    print(client.get_endpoint("record",
                              id="c6894b2c-1856-11e6-9415-3c970ede22b0"))

    # '/buckets/payments/collections/receipts/records/c6894b2c-1856-11e6-9415-3c970ede22b0'


Handling datetime and date objects
----------------------------------

In addition to the data types supported by JSON, kinto-http.py also
supports native Python date and datetime objects.

In case a payload contain a date or a datetime object, kinto-http.py
will encode it as an ISO formatted string.

Please note that this transformation is only one-way. While reading a
record, if a string contains a ISO formated string, kinto-http.py will
not convert it to a native Python date or datetime object.

If you know that a field will be a datetime, you might consider
encoding it yourself to be more explicit about it being a string for
Kinto.



Command-line scripts
--------------------

In order to have common arguments and options for scripts, some utilities are provided
to ease configuration and initialization of client from command-line arguments.

.. code-block:: python

  import argparse
  import logging

  from kinto_http import cli_utils

  logger = logging.getLogger(__name__)

  if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Download records")
      cli_utils.set_parser_server_options(parser)

      args = parser.parse_args()

      cli_utils.setup_logger(logger, args)

      logger.debug("Instantiate Kinto client.")
      client = cli_utils.create_client_from_args(args)

      logger.info("Fetch records.")
      records = client.get_records()
      logger.warn("{} records.".format(len(records)))

The script now accepts basic options:

::

  $ python example.py --help

  usage: example.py [-h] [-s SERVER] [-a AUTH] [-b BUCKET] [-c COLLECTION] [-v]
                    [-q] [-D]

  Download records

  optional arguments:
    -h, --help            show this help message and exit
    -s SERVER, --server SERVER
                          The location of the remote server (with prefix)
    -a AUTH, --auth AUTH  BasicAuth credentials: `token:my-secret` or
                          Authorization header: `Bearer token`
    -b BUCKET, --bucket BUCKET
                          Bucket name.
    -c COLLECTION, --collection COLLECTION
                          Collection name.
    --retry RETRY         Number of retries when a request fails
    --retry-after RETRY_AFTER
                          Delay in seconds between retries when requests fail
                          (default: provided by server)
    -v, --verbose         Show all messages.
    -q, --quiet           Show only critical errors.
    -D, --debug           Show all messages, including debug messages.


Run tests
=========

In one terminal, run a Kinto server:

::

    $ make runkinto

In another, run the tests against it:

::

    $ make tests


(Optional) Install a git hook:

::

    therapist install

Kinto python client
###################

.. image:: https://img.shields.io/travis/Kinto/kinto-http.py.svg
        :target: https://travis-ci.org/Kinto/kinto-http.py

.. image:: https://img.shields.io/pypi/v/kinto-http.svg
        :target: https://pypi.python.org/pypi/kinto-http

.. image:: https://coveralls.io/repos/Kinto/kinto-http.py/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-http.py


Kinto is a service that allows to store and synchronize arbitrary data,
attached to a user account. Its primary interface is HTTP.

*kinto-http* is a Python library that eases the interactions with
a *Kinto* server instance. `A project with related goals is
also available for JavaScript <https://github.com/kinto/kinto.js>`_.


Installation
============

Use pip::

  $ pip install kinto-http


Usage
=====

.. note::

    Operations are always performed directly on the server, and no
    synchronisation features are implemented yet.

- The first version of this API doesn't cache any access nor provide any
  refresh mechanism. If you want to be sure you have the latest data available,
  issue another call.

Here is an overview of what the API provides:

.. code-block:: python

    from kinto_http import Client

    client = Client(server_url="http://localhost:8888/v1",
                    auth=('alexis', 'p4ssw0rd'))

    records = client.get_records(bucket='default', collection='todos')
    for i, record in enumerate(records['data']):
        record['title'] = 'Todo #%d' %i

    for record in records:
        client.update_record(record)

Creating a client
-----------------

The passed `auth` parameter is a `requests <http://docs.python-requests.org>`_
authentication policy, allowing authenticating using whatever scheme fits you
best.

By default, Kinto supports
`Firefox Accounts <https://wiki.mozilla.org/Identity/Firefox_Accounts>`_ and
Basic authentication policies.

.. code-block:: python

    from kinto_http import Client
    credentials = ('alexis', 'p4ssw0rd')

    client = Client(server_url='http://localhost:8888/v1',
                    auth=credentials)

It is also possible to pass the bucket and the collection to the client
at creation time, so that this value will be used by default.

.. code-block:: python

    client = Client(bucket="payments", collection="receipts", auth=auth)


Getting server information
--------------------------

You can use the ``server_info`` method to get the server information::

.. code-block:: python

    from kinto_http import Client

    client = Client(server_url='http://localhost:8888/v1')
    info = client.server_info()
    assert 'schema' in info['capabilities'], "Server doesn't support schema validation."


Handling buckets
----------------

All operations are rooted in a bucket. It makes little sense for
one application to handle multiple buckets at once (but it is possible).
If no specific bucket name is provided, the "default" bucket is used.

.. code-block:: python

    from kinto_http import Client
    credentials = ('alexis', 'p4ssw0rd')

    client = Client(server_url='http://localhost:8888/v1',
                    auth=credentials)
    client.create_bucket('payments')
    client.get_bucket('payments')

    # It is also possible to manipulate bucket permissions (see later)
    client.update_bucket('payments', permissions={})

    # Or delete a bucket and everything under.
    client.delete_bucket('payment')

    # Or even every writable buckets.
    client.delete_buckets()


Collections
-----------

A collection is where records are stored.

.. code-block:: python

    client.create_collection('receipts', bucket='payments')

    # Or get an existing one.
    client.get_collection('receipts', bucket='payments')

    # To delete an existing collection.
    client.delete_collection('receipts', bucket='payments')

    # Or every collections in a bucket.
    client.delete_collections(bucket='payments')

Records
-------

Records can be retrieved from and saved to collections.

A record is a dict with the "permissions" and "data" keys.

.. code-block:: python

    # You can pass a python dictionary to create the record
    # bucket='default' can be omitted since it's the default value

    client.create_record(data={'id': 1234, status: 'done', title: 'Todo #1'},
                         collection='todos', bucket='default')

    # Retrieve all records.
    record = client.get_records(collection='todos', bucket='default')

    # Retrieve a specific record and update it.
    record = client.get_record('89881454-e4e9-4ef0-99a9-404d95900352',
                               collection='todos', bucket='default')
    client.update_record(record, collection='todos', bucket='default')

    # Update multiple records at once.
    client.update_records(records, collection='todos')

    # It is also possible to delete a record.
    client.delete_record(id='89881454-e4e9-4ef0-99a9-404d95900352',
                         collection='todos')

    # Or every records of a collection.
    client.delete_records(collection='todos')

Permissions
-----------

 By default, authors will get read and write access to the manipulated objects.
 It is possible to change this behavior by passing a dict to the `permissions`
 parameter.

 .. code-block:: python

    client.create_record(
        data={'foo': 'bar'},
        permissions={'read': ['group:groupid']},
        collection='todos')

.. note::

    Every creation or modification operation on a distant object can be given
    a `permissions` parameter.

Buckets, collections and records have permissions which can be edited.
For instance to give access to "leplatrem" to a specific record, you would do:

.. code-block:: python

  record = client.get_record(1234, collection='todos', bucket='alexis')
  record['permissions']['write'].append('leplatrem')
  client.update_record(record)

  # During creation, it is possible to pass the permissions dict.
  client.create_record(data={'foo': 'bar'}, permissions={})

Get or create
-------------

In some cases, you might want to create a bucket, collection or record only if
it doesn't exist already. To do so, you can pass the ``if_not_exists=True``
to the ``create_*`` methods::

  client.create_bucket('bucket', if_not_exists=True)

Overwriting existing objects
----------------------------

Most of the methods take a ``safe`` argument, which defaults to ``True``. If set
to ``True`` and a ``if_match`` field is present in the passed ``data``, then a
check will be added to the requests to ensure the record wasn't modified on
the server side in the meantime.

Batching operations
-------------------

Rather than issuing a request for each and every operation, it is possible to
batch the requests. The client will then issue as little requests as possible.

Currently, batching operations only supports write operations, so it is not
possible to do the retrieval of information inside a batch.

It is possible to do batch requests using a Python context manager (``with``):

.. code-block:: python

  with client.batch() as batch:
      for idx in range(0,100):
          batch.update_record(data={'id': idx})

A batch object shares the same methods as another client.

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
<https://kinto.readthedocs.io/en/latest/api/1.x/cliquet/backoff.html#retry-after-indicators>`_.
It is possible (but not recommended) to force this value in the clients:

.. code-block:: python

  client = Client(server_url='http://localhost:8888/v1',
                  auth=credentials,
                  retry=10,
                  retry_after=5)


Generating endpoint paths
-------------------------

You may want to generate some endpoint paths, you can use the
get_endpoint utility to do so:

.. code-block:: python

    client = Client(server_url='http://localhost:8888/v1',
                    auth=('token', 'your-token'),
                    bucket="payments",
                    collection="receipts")
    print(client.get_endpoint("record",
                              id="c6894b2c-1856-11e6-9415-3c970ede22b0"))

    # '/buckets/payments/collections/receipts/records/c6894b2c-1856-11e6-9415-3c970ede22b0'


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
      logger.warn("%s records." % len(records))

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
    -a AUTH, --auth AUTH  BasicAuth token:my-secret
    -b BUCKET, --bucket BUCKET
                          Bucket name.
    -c COLLECTION, --collection COLLECTION
                          Collection name.
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

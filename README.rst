Kinto python client
###################

.. image:: https://img.shields.io/travis/Kinto/kinto-http.py.svg
        :target: https://travis-ci.org/Kinto/kinto-http.py

.. image:: https://img.shields.io/pypi/v/kinto-http.svg
        :target: https://pypi.python.org/pypi/kinto-http

.. image:: https://coveralls.io/repos/Kinto/kinto-http.py/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-http.py


Kinto is a service that allows users to store and synchronize arbitrary data,
attached to a user account. Its primary interface is HTTP.

*kinto-http* is a Python library that eases the interactions with
a *Kinto* server instance. `A project with related goals is
also available for JavaScript <https://github.com/kinto/kinto-http.js>`_.


Installation
============

Use pip::

  $ pip install kinto-http


Usage
=====

.. note::

    Operations are always performed directly on the server, and no
    synchronisation features have been implemented yet.

- The first version of this API doesn't cache any access nor provides any
  refresh mechanism. If you want to be sure you have the latest data available,
  issue another call.

Here is an overview of what the API provides:

.. code-block:: python

    from kinto_http import Client

    client = Client(server_url="http://localhost:8888/v1",
                    auth=('alexis', 'p4ssw0rd'))

    records = client.get_records(bucket='default', collection='todos')
    for i, record in enumerate(records):
        record['title'] = 'Todo {}'.format(i)

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

    auth = ("token", "secret")
    client = Client(bucket="payments", collection="receipts", auth=auth)

After creating a client, you can also replicate an existing one and overwrite
some key arguments.

.. code-block:: python

    client2 = client.clone(collection="orders")

Using FxA from a script with the email/password
-----------------------------------------------

.. code-block:: python

    from fxa.plugins.requests import FxABearerTokenAuth

    auth = FxABearerTokenAuth(
        email, passwd,
        scopes=['kinto'],
        client_id="<FXA-CLIENT-ID>",
        account_server_url='https://api.accounts.firefox.com/v1',
        oauth_server_url='https://oauth.accounts.firefox.com/v1',
    )
    client = Client(bucket="payments", collection="receipts", auth=auth)


Getting server information
--------------------------

You can use the ``server_info`` method to get the server information:

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
    from kinto_http.patch_type import BasicPatch, MergePatch, JSONPatch
    credentials = ('alexis', 'p4ssw0rd')

    client = Client(server_url='http://localhost:8888/v1',
                    auth=credentials)

    # To create a bucket.
    client.create_bucket(id='payments')

    # To get an existing bucket
    bucket = client.get_bucket(id='payments')

    # Or retrieve all readable buckets.
    buckets = client.get_buckets()

    # To create or replace an existing bucket.
    client.update_bucket(id='payments', data={'description': 'My payments data.'})

    # Or modify some fields in an existing bucket.
    # The Kinto server supports different types of patches, which can be used from kinto_http.patch_type.
    client.patch_bucket(id='payments', changes=BasicPatch({'status': 'updated'}))

    # It is also possible to manipulate bucket permissions (see later)
    client.patch_bucket(id='payments', changes=BasicPatch(permissions={}))

    # Or delete a bucket and everything under.
    client.delete_bucket(id='payment')

    # Or even every writable buckets.
    client.delete_buckets()


Groups
------

A group associates a name to a list of principals. It is useful in order to handle permissions.

.. code-block:: python

    # To create a group.
    client.create_group(id='receipts', bucket='payments', data={'members': ['blah', 'foo']})

    # Or get an existing one.
    group = client.get_group(id='receipts', bucket='payments')

    # Or retrieve all groups in the bucket.
    groups = client.get_groups(bucket='payments')

    # To create or replace an existing bucket.
    client.update_group(id='receipts', bucket='payments', 'data'={'members':['foo']})

    # Or modify some fields in an existing group.
    # This uses the server's support for JSON patch, but any patch_type is accepted.
    client.patch_group(id='receipts', bucket='payments',
        changes=JSONPatch([{'op': 'add', 'path': '/data/members/0', 'value': 'ldap:user@corp.com'}]))

    # To delete an existing group.
    client.delete_group(id='receipts', bucket='payments')

    # Or all groups in a bucket.
    client.delete_groups(bucket='payments')


Collections
-----------

A collection is where records are stored.

.. code-block:: python

    # To create a collection.
    client.create_collection(id='receipts', bucket='payments')

    # Or get an existing one.
    collection = client.get_collection(id='receipts', bucket='payments')

    # Or retrieve all of them inside a bucket.
    collections = client.get_collections(bucket='payments')

    # To create or replace an exiting collection.
    client.update_collection(id='receipts', bucket='payments', data={'description':'bleeh'})

    # Or modify some fields of an existing collection.
    client.patch_collection(id='receipts', bucket='payments', changes=MergePatch({'status':'updated'}))

    # To delete an existing collection.
    client.delete_collection(id='receipts', bucket='payments')

    # Or every collections in a bucket.
    client.delete_collections(bucket='payments')


Records
-------

Records can be retrieved from and saved to collections.

A record is a dict with the "permissions" and "data" keys.

.. code-block:: python

    # You can pass a python dictionary to create the record.
    client.create_record(data={'status': 'done', title: 'Todo #1'},
                         collection='todos', bucket='default')

    # You can use id to specify the record id when creating it.
    client.create_record(id='todo2', data={'status': 'doing', 'title': 'Todo #2'},
                         collection='todos', bucket='default')

    # Or get an existing one by its id.
    record = client.get_record(id='todo2', collection='todos', bucket='default')

    # Or retrieve all records.
    records = client.get_records(collection='todos', bucket='default')

    # Or retrieve records timestamp.
    records_timestamp = client.get_records_timestamp(collection='todos', bucket='default')

    # To replace a record using a previously fetched record
    client.update_record(data=record, collection='todos', bucket='default')

    # Or create or replace it by its id.
    client.update_record(data={'status': 'unknown'}, id='todo2', collection='todos', bucket='default')

    # Or modify some fields in an existing record.
    client.patch_record(changes=MergePatch({'assignee': 'bob'}), id='todo2', collection='todos', bucket='default')

    # To delete an existing record.
    client.delete_record(id='89881454-e4e9-4ef0-99a9-404d95900352',
                         collection='todos')

    # Or every records of a collection.
    client.delete_records(collection='todos')

History
-------

If the built-in plugin kinto.plugins.history is enabled, it is possible to access all changes

.. code-block:: python

    # Get the history of a complete bucket
	hist = client.get_history(id='default')
	
	# and activate additional data operations
	hist = client.get_history(id='default',_limit=2, _sort='-last_modified', _since='1533762576015')
	hist = client.get_history(id='default', resource_name='collection')
	
	# Purge the complete history of a bucket
	client.purge_history(id='default')
	
	# Get latest record
	record = client.get_record(id='fe0e8cbb-6074-403e-9017-c8d79192cf0d', collection='todos', bucket='default')
	
	# Get record by its revision id
	record = client.get_record(id='fe0e8cbb-6074-403e-9017-c8d79192cf0d', collection='todos', bucket='default', history_revision='25e6f07b-05b1-4525-b712-efd990ccab2d')
	
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

In some cases, you might want to create a bucket, collection, group or record only if
it doesn't exist already. To do so, you can pass the ``if_not_exists=True``
to the ``create_*`` methods::

  client.create_bucket(id='bucket', if_not_exists=True)

Delete
------

In some cases, you might want to delete a bucket, collection, group or record only if
it exists already. To do so, you can pass the ``if_exists=True``
to the ``delete_*`` methods::

  client.delete_bucket(id='bucket', if_exists=True)

Overwriting existing objects
----------------------------

Most of the methods take a ``safe`` argument, which defaults to ``True``. If set
to ``True`` and a ``last_modified`` field is present in the passed ``data``,
or if the ``if_match`` parameter is specified then a
check will be added to the requests to ensure the record wasn't modified on
the server side in the meantime.

Batching operations
-------------------

Rather than issuing a request for each and every operation, it is possible to
batch the requests. The client will then issue as little requests as possible.

It is possible to do batch requests using a Python context manager (``with``):

.. code-block:: python

  with client.batch() as batch:
      for idx in range(0, 100):
          batch.update_record(data={'id': idx})

Reading data from batch operations is achieved by using the ``results()`` method
available after a batch context is closed.

.. code-block:: python

  with client.batch() as batch:
      batch.get_record('r1')
      batch.get_record('r2')
      batch.get_record('r3')

  r1, r2, r3 = batch.results()

Besides the ``results()`` method, a batch object shares all the same methods as
another client.

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

When the server responses are paginated, the client will download every pages and
merge them transparently.

However, it is possible to specify a limit for the number of items to be retrieved
in one page:

.. code-block:: python

    records = client.get_records(_limit=10)

In order to retrieve every available pages with a limited number of items in each
of them, you can specify the number of pages:

.. code-block:: python

    records = client.get_records(_limit=10, pages=float('inf'))  # Infinity


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
    -a AUTH, --auth AUTH  BasicAuth token:my-secret
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


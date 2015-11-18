Kinto python client
###################

.. image:: https://img.shields.io/travis/Kinto/kinto.py.svg
        :target: https://travis-ci.org/Kinto/kinto.py

.. image:: https://img.shields.io/pypi/v/kinto-client.svg
        :target: https://pypi.python.org/pypi/kinto-client

.. image:: https://coveralls.io/repos/Kinto/kinto.py/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto.py


Kinto is a service that allows to store and synchronize arbitrary data,
attached to a user account. Its primary interface is HTTP.

*kinto-client* is a Python library that eases the interactions with
a *Kinto* server instance. `A project with related goals is
also available for JavaScript <https://github.com/kinto/kinto.js>`_.


Installation
============

Use pip::

  $ pip install kinto-client


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

    from kinto_client import Client

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

    from kinto_client import Client
    credentials = ('alexis', 'p4ssw0rd')

    client = Client(server_url='http://localhost:8888/v1',
                    auth=credentials)

It is also possible to pass the bucket and the collection to the client
at creation time, so that this value will be used by default.

.. code-block:: python

    client = Client(bucket="payments", collection="receipts", auth=auth)


Handling buckets
----------------

All operations are rooted in a bucket. It makes little sense for
one application to handle multiple buckets at once (but it is possible).
If no specific bucket name is provided, the "default" bucket is used.

.. code-block:: python

    from kinto_client import Client
    credentials = ('alexis', 'p4ssw0rd')

    client = Client(server_url='http://localhost:8888/v1',
                    auth=credentials)
    client.create_bucket('payments')
    client.get_bucket('payments')

    # It is also possible to manipulate bucket permissions (see later)
    client.update_bucket('payments', permissions={})


Collections
-----------

A collection is where records are stored.

.. code-block:: python

    client.create_collection('receipts', bucket='payments')

    # Or get an existing one.
    client.get_collection('receipts', bucket='payments')

    # To delete an existing collection.
    client.delete_collection('receipts', bucket='payments')


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

    # It is also possible to delete records.
    client.delete_record(id='89881454-e4e9-4ef0-99a9-404d95900352',
                         collection='todos')

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

Overwriting existing objects
----------------------------

Most of the methods take a ``safe`` argument, which defaults to ``True``. If set
to ``True`` and a ``last_modified`` field is present in the passed ``data``, then a
check will be added to the requests to ensure the record wasn't modified on
the server side in the meantime.

Run tests
=========

In one terminal, run a Kinto server:

::

    $ make runkinto

In another, run the tests against it:

::

    $ make tests

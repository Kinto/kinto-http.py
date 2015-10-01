Kinto python client
###################

Kinto is a service allowing you to store and synchronize arbitrary data,
attached to a user account. Its primary interface is HTTP.

`kinto-client` is a Python library aiming at easing interacting with
a *Kinto* server instance. `A project with related goals is
also available for JavaScript <https://github.com/mozilla-services/cliquetis>`_.

Usage
=====

.. note::

    Operations are always performed directly on the server, and no
    synchronisation features are implemented yet.

- The first version of this API doesn't cache any access nor provide any
  refresh mechanism. If you want to be sure you have the latest data available,
  issue another call.

Here is an overview of what the API looks like:

.. code-block:: python

    from kinto_client import Client

    client = Client(server_url="http://localhost:8888/v1",
                    auth=('alexis', 'p4ssw0rd'))
    records = client.get_records(bucket='default', collection='todos')
    for i, record in enumerate(records):
        record.data.title = 'Todo #%d' %i

    client.update_records(records)


Handling buckets
================

All operations are rooted in a bucket. It makes little sense for
one application to handle multiple buckets at once, but it is possible.

The passed `auth` parameter is a `requests <docs.python-requests.org>`_
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
    client.create_bucket('payments')
    client.get_bucket('payments')

    # It is also possible to manipulate bucket permissions (see later)
    client.update_bucket('payments', permissions={})


Collections
===========

A collection is where records are stored.

.. code-block:: python

    client.create_collection('receipts', bucket='payments')

    # Or get an existing one.
    client.get_collection('receipts', bucket='payments')

    # To delete an existing collection.
    client.delete_collection('receipts', bucket='payments')


Records
=======

Records can be retrieved from and saved to collections.

.. code-block:: python

    # You can pass a python dictionary to create the record
    # bucket='default' can be ommited since it's the default value
    client.create_record({'id': 1234, status: 'done', title: 'Todo #1'},
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
===========

 By default, authors will get read and write access to the manipulated objects.
 It is possible to change this behavior by passing a dict to the `permissions`
 parameter.

 .. code-block:: python

    client.create_record(data={}, permissions={'read': ['group:groupid']},
                         collection='todos')

.. note::

    Every creation or modification operation on a distant object can be given
    a `permissions` parameter.

Buckets, Collections and Groups and records have permissions which can be
edited.

  # Different proposals below.
  # 1. Change the API to return the permissions when asked, in a separate
  # object.
  record, permissions = client.get_record(1234, collection='todos',
                                          include_permissions=True)
  client.update_record(record, permissions=permissions, collection='todos')

  # 2. Allow the mutation of the permissions object, attached to a record.
  record = client.get_record(1234, collection='todos')
  record.permissions.write += ['leplatrem', ]
  client.update_record(record)

  # In any case, for the creation it will be possible to pass the permissions.
  client.create_record(record, permissions={})
  

Installation
============

To install the kinto client, use pip::

  $ pip install kinto_client

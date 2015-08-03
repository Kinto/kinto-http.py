Kinto python client
###################

Kinto is a service allowing you to store and synchronize arbitrary data,
attached to a user account. Its primary interface is HTTP.

`kinto-client` is a Python library aiming at easing interacting with
a *Kinto* server instance. `A project with related goals is
also available for JavaScript <https://github.com/mozilla-services/cliquetis>`_.

.. warning::

    Everything described here is still pure fiction and no implementation
    of this is ready to be used yet.


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

    from kintoclient import Bucket

    bucket = Bucket('default', server_url='http://localhost:8888/v1',
                    auth=('alexis', 'p4ssw0rd'))
    todo = bucket.get_collection('todo')

    records = todo.get_records()
    for i, record in enumerate(records):
        record.data.title = 'Todo #%d' %i

    todo.save_records(records)


Handling buckets
================

All operations are rooted in a bucket. It makes little sense for
one application to handle multiple buckets at once.

The passed `auth` parameter is a `requests <docs.python-requests.org>`_
authentication policy, allowing authenticating using whatever fits you best.

By default, Kinto supports
`Firefox Accounts <https://wiki.mozilla.org/Identity/Firefox_Accounts>`_ and
Basic authentication policies.

.. code-block:: python

    credentials = ('alexis', 'p4ssw0rd')

    bucket = Bucket('payments', server_url='http://localhost:8888/v1',
                    auth=credentials)

    # Passing `create=True` to the bucket will make an HTTP request to
    # create it.
    bucket = Bucket('payments', server_url='http://localhost:8888/v1',
                    auth=credentials, create=True)


Collections
===========

A collection is where records are stored.

.. code-block:: python

    # Once the bucket handy, use it to handle collections or groups.
    collection = bucket.create_collection('receipts')

    # Or get an existing one.
    collection = bucket.get_collection('receipts')

    # To delete an existing collection.
    bucket.delete_collection('receipts')


Records
=======

Records can be retrieved from and saved to collections.

.. code-block:: python

    # Create an empty record
    record = collection.create_record()

    # You can also pass a python dictionary to represent the record
    record = collection.create_record(dict(id='XXX', status='done',
                                           title='Todo #1'))

    # Get all records
    record = collection.get_all_records()
    record = collection.get_record(id='89881454-e4e9-4ef0-99a9-404d95900352')
    collection.save_record(record)
    collection.save_records([record1, record2])
    collection.delete_record(id='89881454-e4e9-4ef0-99a9-404d95900352')
    collection.delete_records([record1, record2])


Permissions
===========

 By default, authenticated users will get read and write access to the
 manipulated objects. It is possible to change this behavior by passing a dict
 to the `permissions` parameter.

 .. code-block:: python

    record = collection.create_record(
        data={},
        permissions={'read': ['group:groupid']})

.. note::

    Every creation or modification operation on a distant object can be given
    a `permissions` parameter.

The `Bucket`, `Collection`, `Group` and `Record` classes have a special
`permissions` object that can be mutated in order to update the permissions
model attached to the object.

.. code-block:: python

    bucket = Bucket('default', auth=('alexis', 'p4ssw0rd'))

    # XXX We need to find a way to get other's names from kinto, this isn't
    # realistic.
    friends = ['natim', 'niko', 'mat', 'tarek']
    bucket.permissions.write += friends
    bucket.permissions.create_collection += friends

    # You *need* to call save in order to have these changes reflected in the
    # remote.
    bucket.permissions.save()

    # or if you want to save the whole bucket:
    bucket.save()

Groups
======

Giving specific permissions to specific users can be handy sometimes, but
quickly becomes a pain to maintain if many permissions need to be given to
different sets of people.

In order to handle this better, Kinto has a concept of groups. Groups represent
a set of individuals, described by a name. Individuals can then be added and
removed from the group, and permissions can be given to the group rather than
the individuals.

.. note::

    Groups are attached to a bucket (and not to a collection). As such they
    can be shared accross different collections of the same bucket.

Groups can be manipulated like python lists.

.. code-block:: python

    group = bucket.create_group('moderators', ['list', 'of', 'users'])
    group.add('niko')
    group.remove('remy')
    group.clear()  # Remove everyone in the group
    group.save()


Sending requests in batch
=========================

Sometimes, it is useful to issue multiple operations in batch, to avoid
sending many requests to the same server. This is especially useful when
operations have been done offline and the server needs a refresh.

Batch operations can be done using a Python context manager (the `with`
statement).

Under the hood, a `Session` class is instanciated when you first create a
bucket. It is possible to pass the session to the constructor of the `Bucket`.

.. code-block:: python

    from kintoclient import BatchSession, Bucket
    session = BatchSession()

    my_bucket = Bucket('personal', session=session, create=True)
    for collection in range(5):
        my_bucket.create_collection("toto-%s" % collection, create=True)
    session.execute()


Installation
============

To install the kinto client, use pip::

  $ pip install kintoclient

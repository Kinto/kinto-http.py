Kinto python client
###################

Python library to interact with a `Kinto <https://kinto.readthedocs.org>`_
HTTP server.

Usage
=====

.. warning::
    The approach this library takes is different from the one took in the
    `Cliquetis <https://github.com/mozilla-services/cliquetis>`_ javascript
    client: Operations are always performed directly on the server, and no
    synchronisation features are implemented yet.

- Every operation is done remotely; No synchronisation operation is supported;
- 

To create a bucket and a collection (needed to use them later):

.. code-block:: python

    import kintoclient import Bucket

    # First, create a bucket.
    bucket = Bucket(name='payments', server_url='http://localhost:8888/v1',
                    auth=credentials, create=True)

    # In case it already exists, you can just retrieve it.
    bucket = Bucket(name='payments', server_url='http://localhost:8888/v1',
                    auth=credential)

    # Handling collections
    collection = payments.create_collection(name='receipts')
    collection = payments.get_collection(name='receipts')
    collection.destroy() # Deletes the collection.
    bucket.delete_collection(name='receipts')

    # Handling records
    record = collection.create_record(data={})
    record = collection.get_all_records()
    record = collection.get_record()
    collection.save_record(record)  # Issues a PUT or PATCH
    collection.delete_record(record)
    collection.delete_records([record1, record2])

    # Permissions on records
    # Makes the record avail. to everyone.
    record = collection.create_record(data={}, public=True)
    record = collection.create_record(
      data={},
      permissions={'read': ['group:groupid']})
    collection.update_record_permissions(id=1234, read=['basicauth_kumar', ])

    record.update_record_permissions(read=['basicauth_kumar', ])
    record.permissions.read += 'group:friends'
    record.permissions.write = ['group:friends', 'basicauth_kumar']

    # Handling groups
    collection.create_group(name='moderators', ['list', 'of', 'users'])
    collection.add_to_group(name='moderators', ['foo', 'bar'])
    collection.remove_from_group(name='moderators', ['foo'])
    collection.delete_group(name='moderators')
    collection.clear_group(name='moderators')  # Removes all members of a group.

    # create_group can also handles its permissions
    collection.create_group(name='moderators', ['list', 'of', 'users'],
        permissions={
          'write': ['list', 'of', 'principals'],
        })

    # Permissions on buckets
    bucket.permissions.record_create = ['list', 'of', 'principals']
    bucket.permissions.group_create = ['list', 'of', 'principals']
    bucket.permissions.group_write = []
    bucket.permissions.group_read = []
    bucket.permissions.record_write = []
    bucket.permissions.record_read = []

    # Should we repeat "bucket" here?
    # Should it be record_create or record_creators ?
    bucket.update_permissions(record_create=['list',])


Installation
============

To install the kinto client, it's simple, just use pip!::

  $ pip install kintoclient


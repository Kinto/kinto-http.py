Kinto Python client
###################

.. image:: https://github.com/Kinto/kinto-http.py/actions/workflows/test.yml/badge.svg
        :target: https://github.com/Kinto/kinto-http.py/actions

.. image:: https://img.shields.io/pypi/v/kinto-http.svg
        :target: https://pypi.python.org/pypi/kinto-http

*kinto-http* is the Python library to interact with a `Kinto <https://kinto.readthedocs.io>`_ server.

A similar `client written in JavaScript <https://github.com/Kinto/kinto.js>`_ is also available.


.. contents::
   :local:
   :depth: 2


Installation
============

Use pip::

  $ pip install kinto-http


Quickstart
==========

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(server_url="http://localhost:8888/v1",
                               auth=("alexis", "p4ssw0rd"))

    records = client.get_records(bucket="default", collection="todos")
    for i, record in enumerate(records):
        record["title"] = "Todo {}".format(i)
        client.update_record(data=record)


Instantiating a client
======================

The ``auth`` parameter accepts any `requests <https://docs.python-requests.org>`_
authentication policy.

By default, a simple tuple is converted to a ``Basic Auth`` ``Authorization`` header, which
can authenticate users via `Kinto Accounts <https://kinto.readthedocs.io/en/stable/api/1.x/accounts.html>`_.

.. code-block:: python

    import kinto_http

    auth = ("alexis", "p4ssw0rd")

    client = kinto_http.Client(server_url="http://localhost:8888/v1",
                               auth=auth)

A ``bucket`` ID and/or ``collection`` ID can also be passed as default values for the
parameters of subsequent client operations:

.. code-block:: python

    client = kinto_http.Client(bucket="payments", collection="receipts", auth=auth)

After creating a client, you can also clone an existing one and override some
of its arguments:

.. code-block:: python

    client2 = client.clone(collection="orders")

An asynchronous client is also available. It exposes the same endpoints as the
synchronous client, except for batch operations:

.. code-block:: python

    from kinto_http import AsyncClient

    auth = ("alexis", "p4ssw0rd")

    client = AsyncClient(server_url="http://localhost:8888/v1", auth=auth)
    info = await client.server_info()
    assert "schema" in info["capabilities"], "Server doesn't support schema validation."


Dry mode
--------

The ``dry_mode`` parameter can be set to simulate requests without actually
sending them over the network. When enabled, the client makes no external
calls and logs the requests at the ``DEBUG`` level instead. This is useful for
testing and debugging.

.. code-block:: python

    client = kinto_http.Client(server_url="http://localhost:8888/v1", dry_mode=True)


Authentication
==============

Bearer access token (OpenID)
----------------------------

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(auth=kinto_http.BearerTokenAuth("XYPJTNsFKV2"))


The ``Authorization`` header is prefixed with ``Bearer`` by default. If the ``header_type``
is `customized on the server <https://kinto.readthedocs.io/en/stable/configuration/settings.html#openid-connect>`_,
the client must specify the expected type:

.. code-block:: python

    kinto_http.BearerTokenAuth("XYPJTNsFKV2", type="Bearer+OIDC")

.. note::

    Passing a string that starts with ``Bearer`` automatically instantiates a
    ``kinto_http.BearerTokenAuth()`` object.

    In other words, ``kinto_http.Client(auth="Bearer+OIDC XYPJTNsFKV2")`` is equivalent
    to ``kinto_http.Client(auth=kinto_http.BearerTokenAuth("XYPJTNsFKV2", type="Bearer+OIDC"))``.


Browser-based OAuth
-------------------

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(server_url="http://localhost:8888/v1",
                               auth=kinto_http.BrowserOAuth())

The client opens a browser page and catches the bearer token obtained after
the OAuth dance.

A specific provider can be selected by name:

.. code-block:: python

    auth = kinto_http.BrowserOAuth(provider="google")


Custom headers
==============

Custom headers can be specified in the client constructor and will be sent
with every request:

.. code-block:: python

    import kinto_http

    client = kinto_http.Client(server_url="http://server/v1", headers={
        "Allow-Access": "CDN",
        "User-Agent": "blocklist-updater"
    })


Getting server information
==========================

Use the ``server_info()`` method to fetch the server information. The response
is cached on the client for subsequent calls.

.. code-block:: python

    from kinto_http import Client

    client = Client(server_url="http://localhost:8888/v1")
    info = client.server_info()
    assert "schema" in info["capabilities"], "Server doesn't support schema validation."


API operations
==============

Buckets
-------

* ``get_bucket(id=None, **kwargs)``: retrieve a single bucket
* ``get_buckets(**kwargs)``: retrieve all readable buckets
* ``create_bucket(id=None, data=None, **kwargs)``: create a bucket
* ``update_bucket(id=None, data=None, **kwargs)``: create or replace an existing bucket
* ``patch_bucket(id=None, changes=None, **kwargs)``: modify some fields of an existing bucket
* ``delete_bucket(id=None, **kwargs)``: delete a bucket and everything under it
* ``delete_buckets(**kwargs)``: delete all writable buckets


Groups
------

* ``get_group(id=None, bucket=None, **kwargs)``: retrieve a single group
* ``get_groups(bucket=None, **kwargs)``: retrieve all readable groups
* ``create_group(id=None, data=None, bucket=None, **kwargs)``: create a group
* ``update_group(id=None, data=None, bucket=None, **kwargs)``: create or replace an existing group
* ``patch_group(id=None, changes=None, bucket=None, **kwargs)``: modify some fields of an existing group
* ``delete_group(id=None, bucket=None, **kwargs)``: delete a group
* ``delete_groups(bucket=None, **kwargs)``: delete all writable groups of a bucket


Collections
-----------

* ``get_collection(id=None, bucket=None, **kwargs)``: retrieve a single collection
* ``get_collections(bucket=None, **kwargs)``: retrieve all readable collections
* ``create_collection(id=None, data=None, bucket=None, **kwargs)``: create a collection
* ``update_collection(id=None, data=None, bucket=None, **kwargs)``: create or replace an existing collection
* ``patch_collection(id=None, changes=None, bucket=None, **kwargs)``: modify some fields of an existing collection
* ``delete_collection(id=None, bucket=None, **kwargs)``: delete a collection and everything under it
* ``delete_collections(bucket=None, **kwargs)``: delete all writable collections of a bucket


Records
-------

* ``get_record(id=None, bucket=None, collection=None, **kwargs)``: retrieve a single record
* ``get_records(bucket=None, collection=None, **kwargs)``: retrieve all readable records
* ``get_paginated_records(bucket=None, collection=None, **kwargs)``: iterate over paginated records
* ``get_records_timestamp(bucket=None, collection=None, **kwargs)``: return the current timestamp of the collection of records
* ``create_record(id=None, data=None, bucket=None, collection=None, **kwargs)``: create a record
* ``update_record(id=None, data=None, bucket=None, collection=None, **kwargs)``: create or replace an existing record
* ``patch_record(id=None, changes=None, bucket=None, collection=None, **kwargs)``: modify some fields of an existing record
* ``delete_record(id=None, bucket=None, collection=None, **kwargs)``: delete a record
* ``delete_records(bucket=None, collection=None, **kwargs)``: delete all writable records of a collection


Permissions
===========

The permissions on an object can be specified or modified by passing a ``permissions``
argument to the ``create_*()``, ``patch_*()``, or ``update_*()`` methods:

.. code-block:: python

    client.create_record(data={"foo": "bar"},
                         permissions={"read": ["group:groupid"]})


    record = client.get_record("123", collection="todos", bucket="alexis")
    record["permissions"]["write"].append("leplatrem")
    client.update_record(data=record)


To obtain the list of all permissions across every object, use the ``get_permissions()`` method:

.. code-block:: python

    all_perms = client.get_permissions(exclude_resource_names=("record",))

    has_collection_perms = any(
        p for p in all_perms
        if p["collection_id"] == "my-collection"
        and "write" in p["permissions"]
    )


Get or create
=============

To create a bucket, collection, group, or record only if it doesn't already exist,
pass ``if_not_exists=True`` to the ``create_*()`` methods:

.. code-block:: python

  client.create_bucket(id="blog", if_not_exists=True)
  client.create_collection(id="articles", bucket="blog", if_not_exists=True)


Delete if exists
================

To delete a bucket, collection, group, or record only if it exists,
pass ``if_exists=True`` to the ``delete_*()`` methods:

.. code-block:: python

  client.delete_bucket(id="bucket", if_exists=True)


Patch operations
================

The ``patch_*()`` methods accept a ``changes`` argument, which must be one of
``BasicPatch``, ``MergePatch``, or ``JSONPatch``:

.. code-block:: python

    from kinto_http.patch_type import BasicPatch, MergePatch, JSONPatch


    # Replace specified attributes on the resource.
    client.patch_record(id="abc", changes=BasicPatch({"over": "write"}))

    # Recursively merge attributes. Setting a field to ``None`` removes it.
    client.patch_record(id="todo", changes=MergePatch({"assignee": "bob"}))

    # Apply a JSON Patch (RFC 6902) sequence of operations.
    client.patch_record(id="receipts", changes=JSONPatch([
        {"op": "add", "path": "/data/members/0", "value": "ldap:user@corp.com"}
    ]))


Concurrency control
===================

The ``create_*()``, ``patch_*()``, and ``update_*()`` methods take a ``safe``
argument (default: ``True``).

When ``safe=True``, the client ensures that the object does not already exist
(for creations) or has not been modified server-side since it was fetched
(for updates and patches). The timestamp is read implicitly from the
``last_modified`` field of the supplied ``data``, or explicitly via the
``if_match`` parameter.


Batching operations
===================

Rather than issuing one request per operation, multiple operations can be
batched into a single request (sync client only).

Use the ``batch()`` method as a context manager:

.. code-block:: python

  with client.batch() as batch:
      for idx in range(0, 100):
          batch.update_record(data={"id": idx})

.. note::

    Aside from the ``results()`` method, a batch object exposes the same
    methods as a regular client.

The responses of batched operations are read via the ``results()`` method,
available after the batch context exits:

.. code-block:: python

  with client.batch() as batch:
      batch.get_record("r1")
      batch.get_record("r2")
      batch.get_record("r3")

  r1, r2, r3 = batch.results()

By default, an exception is raised if any operation in the batch returns a 4xx
response. To allow these to be ignored (eg. for bulk inserts where some records
may already exist), pass ``ignore_batch_4xx=True`` to the ``Client``
constructor.


Errors
======

Failing operations raise a ``KintoException``, which carries ``request`` and
``response`` attributes:

.. code-block:: python

    import kinto_http

    try:
        client.create_group(id="friends")
    except kinto_http.KintoException as e:
        if e.response and e.response.status_code == 403:
            print("Not allowed!")

The following more specific exceptions are also exported:

* ``BucketNotFound``: raised when a bucket is missing.
* ``CollectionNotFound``: raised when a collection is missing.
* ``KintoBatchException``: raised when one or more operations in a batch fail. It
  exposes ``exceptions`` (the list of failures) and ``results`` (the responses of
  successful operations).


Request timeout
===============

A ``timeout`` value, in seconds, can be specified in the client constructor:

.. code-block:: python

    client = Client(server_url="...", timeout=5)

To distinguish the connect timeout from the read timeout, use a tuple:

.. code-block:: python

    client = Client(server_url="...", timeout=(3.05, 27))

For an infinite timeout, use ``None`` (the default):

.. code-block:: python

    client = Client(server_url="...", timeout=None)

See the `timeout documentation <https://requests.readthedocs.io/en/latest/user/advanced/#timeouts>`_
of the underlying ``requests`` library.


Retry on error
==============

When the server is throttled (under heavy load or maintenance), it may return
error responses. The client can retry the same request until it succeeds.
To enable retries, specify the maximum number on the client:

.. code-block:: python

  client = Client(server_url="http://localhost:8888/v1",
                  auth=credentials,
                  retry=10)

The Kinto protocol lets the server `define the duration in seconds between retries
<https://kinto.readthedocs.io/en/latest/api/1.x/backoff.html>`_.
This value can be forced from the client (not recommended):

.. code-block:: python

  client = Client(server_url="http://localhost:8888/v1",
                  auth=credentials,
                  retry=10,
                  retry_after=5)


Pagination
==========

When the server returns paginated responses, the client downloads every page
and merges them transparently:

.. code-block:: python

    records = client.get_records()

The ``get_paginated_records()`` method returns a generator that yields each page:

.. code-block:: python

  for page in client.get_paginated_records():
      records = page["data"]

To control the number of items per page, use ``_limit``:

.. code-block:: python

    records = client.get_records(_limit=10)

To fetch all available pages with a limited number of items per page,
combine ``_limit`` with ``pages``:

.. code-block:: python

    records = client.get_records(_limit=10, pages=float("inf"))  # Infinity


History
=======

If the built-in `history plugin <https://kinto.readthedocs.io/en/latest/api/1.x/history.html>`_
is enabled, the history of changes can be retrieved:

.. code-block:: python

    # Get the complete history of a bucket
    changes = client.get_history(bucket="default")

    # Or apply filters
    hist = client.get_history(bucket="default", _limit=2, _sort="-last_modified", _since="1533762576015")
    hist = client.get_history(bucket="default", resource_name="collection")


The history of a bucket can also be purged:

.. code-block:: python

    client.purge_history(bucket="default", _before='"1743671651423"', user_id="account:fulanito")


Attachments
===========

If the `kinto-attachment plugin <https://github.com/Kinto/kinto-attachment/>`_
is enabled, attachments can be uploaded, downloaded, and removed on records.

Download an attachment:

.. code-block:: python

    filepath = client.download_attachment(record_obj)

Options:

- ``filepath``: path to the file or directory where the attachment should be saved.
  If a directory is provided, the original filename is used.
- ``filename``: name of the file to save the attachment as. If not provided, the
  original filename is used.
- ``overwrite`` (default: ``False``): if a file already exists locally, the
  download is skipped when its size and hash match the remote attachment.
- ``save_metadata`` (default: ``False``): if ``True``, the attachment metadata
  (the ``attachment`` field of the record) is saved alongside the file as a
  ``.meta.json`` file.
- ``chunk_size`` (default: 8192): the chunk size, in bytes, used to stream the download.

Upload an attachment:

.. code-block:: python

    client.add_attachment(id="record-id", filepath="/path/to/image.png")

Remove an attachment:

.. code-block:: python

    client.remove_attachment(id="record-id")


Signing workflow
================

If the `kinto-signer plugin <https://github.com/Kinto/kinto-signer>`_ is enabled,
the following methods help to drive the review workflow on a collection:

.. code-block:: python

    client.request_review(id="my-collection", bucket="main-workspace", message="please review")
    client.approve_changes(id="my-collection", bucket="main-workspace")
    client.decline_changes(id="my-collection", bucket="main-workspace", message="not ready")
    client.rollback_changes(id="my-collection", bucket="main-workspace", message="reverting")

The signed contents of a destination collection can be retrieved via:

.. code-block:: python

    changeset = client.get_changeset(bucket="main", collection="my-collection")

Pass ``bust_cache=True`` to bypass any HTTP cache on the way.


Endpoint URLs
=============

The ``get_endpoint()`` method returns the URL of a resource on the server:

.. code-block:: python

    client = Client(server_url="http://localhost:8888/v1",
                    auth=("token", "your-token"),
                    bucket="payments",
                    collection="receipts")

    print(client.get_endpoint("record",
                              id="c6894b2c-1856-11e6-9415-3c970ede22b0"))

    # '/buckets/payments/collections/receipts/records/c6894b2c-1856-11e6-9415-3c970ede22b0'


Handling datetime and date objects
==================================

In addition to the data types supported by JSON, *kinto-http* also accepts
native Python ``date`` and ``datetime`` objects in payloads, and encodes them
as ISO-formatted strings.

This transformation is one-way: when reading a record, ISO-formatted strings
are *not* converted back to native Python ``date`` or ``datetime`` objects. If
you know that a field contains a datetime, consider encoding it yourself for
clarity.


Command-line scripts
====================

The ``cli_utils`` module provides helpers to share common arguments and options
across scripts and to initialize a client from command-line arguments:

.. code-block:: python

  import argparse
  import logging

  from kinto_http import cli_utils

  logger = logging.getLogger(__name__)

  if __name__ == "__main__":
      parser = argparse.ArgumentParser(description="Download records")
      cli_utils.add_parser_options(parser)

      args = parser.parse_args()

      cli_utils.setup_logger(logger, args)

      logger.debug("Instantiate Kinto client.")
      client = cli_utils.create_client_from_args(args)

      logger.info("Fetch records.")
      records = client.get_records()
      logger.warning("{} records.".format(len(records)))

The script automatically supports a basic set of options:

::

  $ python example.py --help

  usage: example.py [-h] [-s SERVER] [-a AUTH] [-b BUCKET] [-c COLLECTION]
                    [--retry RETRY] [--retry-after RETRY_AFTER]
                    [--ignore-batch-4xx] [-v] [-q] [-D]

  Download records

  options:
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
    --ignore-batch-4xx    Do not fail on 4xx errors in batch requests.
    -v, --verbose         Show all messages.
    -q, --quiet           Show only critical errors.
    -D, --debug           Show all messages, including debug messages.


Development
===========

See `contributing docs <./.github/CONTRIBUTING.md>`_.

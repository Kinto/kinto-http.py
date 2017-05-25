CHANGELOG
#########

This document describes changes between each past release.


9.1.0 (unreleased)
==================

- Nothing changed yet.


9.0.0 (2017-05-25)
==================

**Breaking changes**

- The client will fail a batch only when a 5XX error occurs (#148)

**New Features**

- Log all the batch responses (#148)
- Log the request and the batch responses in debug (#148)
- Allow reading responses from batch requests with the ``results()`` method. (#146)


8.0.1 (2017-05-16)
==================

**Bug fixes**

- Fix get_records_timestamp JSONDecode error while trying to decode
  the body of a HEAD response. (#144)


8.0.0 (2017-05-11)
==================

**Breaking changes**

- Fetch only one page when ``_limit`` is specified and allow to override this
  with a ``pages`` argument (fixes #136)
- Make client methods API consistent by forcing keyword parameters (#119)
- Deduce the ``id`` of a resource with the value of ``id`` in ``data`` if present (#143)
- Drop Python 2.7 support. Now supports Python 3.5+

**New Features**

- Keep tracks of Backoff headers and raise an ``BackoffException`` if
  we are not waiting enough between two calls. (#53)
- Add ``--retry`` and ``--retry-after`` to CLI utils helpers (fixes #126)

**Bug fixes**

- Fix retry behaviour when responses are successful (fixes #129)
- Fix Retry-After value to be read as integer rather than string. (#131)
- Fix No JSON could be decoded ValueError (fixes #116)

**Internal changes**

- ``make tests-once`` to run functional tests in order to calculate coverage correctly (#131)


7.2.0 (2017-03-17)
==================

- Only provide the `data` JSON field when data is provided. (#122)


7.1.0 (2017-03-16)
==================

**Bug fixes**

- Method for plural endpoints now return list of objects instead of ``odict_values``.

**New features**

- Add logging (fixes #36, #110, thanks @sahildua2305)

**Documentation**

- Fix explanation about safe/if_match/last_modified
- Fix missing methods in docs (#102, thanks @gabisurita)
- Improve contributing guide (#104, #111,  thanks @Sayli-Karnik)
- Show how to use the FxABearerTokenAuth auth (#117)


7.0.0 (2016-09-30)
==================

**Breaking changes**

- Removed ``if_exists`` argument from the ``delete_*s`` methods for plural endpoints
  (#98, thanks @mansimarkaur!)

**New features**

- Added CRUD methods for the group endpoints (#95, thanks @mansimarkaur!)

**Documentation**

- Add contributing guide (#90, thanks @sahildua2305!)


6.2.1 (2016-09-08)
==================

**New features**

- Add a ``if_exists`` flag to delete methods to avoid raising if the
  item was already deleted. (#82)
- Improving the ``clone`` method to keep all the previous parameters values
  if missing as parameters. (#91)


6.1.0 (2016-08-04)
==================

**New features**

- Add a ``get_records_timestamp`` method to get the collection ``ETag``. (#81)


6.0.0 (2016-06-10)
==================

**Breaking changes**

- Rename kinto_client to kinto_http (#74)


5.0.0 (2016-05-12)
==================

**Breaking changes**

- Rename the ``last_modified`` client parameter into ``if_match`` (#68)

**New features**

- Display a better message when having 403 on create_collection and
  create_record methods (#49)
- Expose ``get_endpoints`` as part of the client API (#60)
- Add a ``server_info`` method to retrieve the root url info (#70)

**Internal changes**

- Rename the Batch class into BatchSession (#52)
- Change readthedocs.org urls in readthedocs.io (#71)


4.1.0 (2016-04-26)
==================

**New features**

- Add new methods ``get_buckets()``, ``delete_buckets()``, ``delete_bucket()``,
  ``delete_collections()``, ``delete_records()``, ``patch_record()`` (#55)

**Internal changes**

- Functional tests are now tested on Kinto master version (#65)


4.0.0 (2016-03-08)
==================

**Breaking changes**

- The function ``cli_utils.set_parser_server_options()`` was renamed
  ``cli_utils.add_parser_options()`` (#63)


**New features**

- ``add_parser_options`` can now exclude bucket and collection
  parameters. (#63)
- ``create_client_from_args`` can now works even with no bucket or
  collection arguments (#63)


**Bug fixes**

- Do not sent body in GET requests. (#62)


3.1.0 (2016-02-16)
==================

**New features**

- Add CLI helpers to configure and instantiate a Client from command-line arguments
  (#59)


3.0.0 (2016-02-10)
==================

**Breaking changes**

- Updated the ``update_collection()`` signature: data is now the fisr argument
  (#47)

**New features**

- Added a retry option for batch requests (#51)
- Use the "default" bucket if nothing is specified (#50)
- Added a ``if_not_exists`` argument to the creation methods (#42)
- Added a replication mechanism in ``kinto_http.replication`` (#26)
- Handle the ``last_modified`` argument on update or create operations (#24)

**Bug fixes**

- Do not force the JSON content-type in requests if multipart-encoded files are
  sent (#27)
- Fail the batch operations early (#47)
- Remove un-needed requirements (FxA) (#43)
- Use ``max_batch_request`` from the server to issue more than one batch request
  (#30)
- Make sure batch raises an error when needed (#28)
- Fix an invalid platform error for some versions of python (#31)
- Do not lowercase valid IDs (#33)

**Documentation**

- Add documentation about client.batch (#44)


2.0.0 (2015-11-18)
==================

- Added support for pagination in records requests (#13)
- Added support for If-Match / If-None-Match headers for not overwriting
  existing records (#14)
- Changed the API of the batch support. There is now a ``client.batch()`` context
  manager (#17)
- Added support of the PATCH methods to update records / collections (#19)


1.0.0 (2015-11-09)
==================

**Breaking changes**

- Rewrote the API to be easier to use (#10)


0.2.0 (2015-10-28)
==================

**Breaking changes**

- Rename kintoclient to kinto_client (#8)

**Features**

- Add the endpoints class. (#9)
- Add batching utilities. (#9)

**Internal changes**

- Add universal wheel configuration.


0.1.1 (2015-09-03)
==================

**Initial version**

- A client to synchroneously call a Kinto server.

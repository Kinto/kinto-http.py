CHANGELOG
#########

This document describes changes between each past release.


4.1.0 (unreleased)
==================

- Nothing changed yet.


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
- Added a replication mechanism in ``kinto_client.replication`` (#26)
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

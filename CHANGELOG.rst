CHANGELOG
#########

This document describes changes between each past release.


2.1.0 (unreleased)
==================

- Nothing changed yet.


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

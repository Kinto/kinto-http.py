import re
import sys

import pkg_resources


kinto_http_version = pkg_resources.get_distribution("kinto_http").version
requests_version = pkg_resources.get_distribution("requests").version
python_version = ".".join(map(str, sys.version_info[:3]))

USER_AGENT = "kinto_http/{} requests/{} python/{}".format(
    kinto_http_version, requests_version, python_version
)
OBJECTS_PERMISSIONS = {
    "bucket": ["group:create", "collection:create", "write", "read"],
    "group": ["write", "read"],
    "collection": ["write", "read", "record:create"],
    "record": ["read", "write"],
}
ID_FIELD = "id"
DO_NOT_OVERWRITE = {"If-None-Match": "*"}
VALID_SLUG_REGEXP = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")

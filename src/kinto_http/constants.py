import re
import sys
import importlib.metadata


kinto_http_version = importlib.metadata.version("kinto_http")
requests_version = importlib.metadata.version("requests")
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
SERVER_URL = "http://localhost:8888/v1"
DEFAULT_AUTH = ("user", "p4ssw0rd")
ALL_PARAMETERS = [
    ["-h", "--help"],
    ["-s", "--server"],
    ["-a", "--auth"],
    ["-b", "--bucket"],
    ["-c", "--collection"],
    ["--retry"],
    ["--retry-after"],
    ["--ignore-batch-4xx"],
    ["-v", "--verbose"],
    ["-q", "--quiet"],
    ["-D", "--debug"],
]

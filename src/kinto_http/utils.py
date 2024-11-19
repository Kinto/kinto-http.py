import functools
import json
import re
import sys
import unicodedata
from datetime import date, datetime

from unidecode import unidecode

from kinto_http.constants import VALID_SLUG_REGEXP


MAX_LENGTH_INT = len(str(sys.maxsize * 2 + 1))


def slugify(value):
    """Normalizes string, converts to lowercase, removes non-alpha characters
    and converts spaces to hyphens.
    """
    value = str(value)
    # Do not slugify valid values.
    if VALID_SLUG_REGEXP.match(value):
        return value

    value = unidecode(value)
    if isinstance(value, bytes):
        value = value.decode("ascii")  # pragma: nocover
    value = unicodedata.normalize("NFKD", value).lower()
    value = re.sub("[^\\w\\s-]", "", value.lower()).strip()
    value = re.sub("[-\\s]+", "-", value)
    return value


def urljoin(server_url, path):
    """Return the url concatenation of server_url and path."""
    return server_url.rstrip("/") + "/" + path.lstrip("/")


def quote(text):
    if hasattr(text, "strip"):
        text = text.strip('"')
    return '"{0}"'.format(text)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.
    Source: http://stackoverflow.com/a/312464
    """
    if n > 0:
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    else:
        yield lst


def json_iso_datetime(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s is not serializable" % type(obj))


json_dumps = functools.partial(json.dumps, default=json_iso_datetime)


def sort_records(records, sort):
    """
    Sort records following the same format as the server ``name,-last_modified``.
    """

    def reversed(way, value):
        if isinstance(value, (int, float)):
            value = str(way * value).zfill(MAX_LENGTH_INT)
        if isinstance(value, str):
            return "".join(chr(255 - ord(c)) for c in value) if way < 0 else value
        return str(value)

    sort_fields = [
        (-1, f.strip()[1:]) if f.startswith("-") else (1, f.strip()) for f in sort.split(",")
    ]
    return sorted(
        records, key=lambda r: tuple(reversed(way, r.get(field)) for way, field in sort_fields)
    )

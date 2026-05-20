import functools
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from typing import Any, Iterable, Iterator, List, Tuple

from unidecode import unidecode

from kinto_http.constants import VALID_SLUG_REGEXP


MAX_LENGTH_INT = len(str(sys.maxsize * 2 + 1))


def slugify(value: Any) -> str:
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


def urljoin(server_url: str, path: str) -> str:
    """Return the url concatenation of server_url and path."""
    return server_url.rstrip("/") + "/" + path.lstrip("/")


def quote(text: Any) -> str:
    if hasattr(text, "strip"):
        text = text.strip('"')
    return '"{0}"'.format(text)


def chunks(lst: List[Any], n: int) -> Iterator[List[Any]]:
    """Yield successive n-sized chunks from lst.
    Source: http://stackoverflow.com/a/312464
    """
    if n > 0:
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    else:
        yield lst


def json_iso_datetime(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s is not serializable" % type(obj))


json_dumps = functools.partial(json.dumps, default=json_iso_datetime)


def sort_records(records: List[dict], sort: str) -> List[dict]:
    """
    Sort records following the same format as the server ``name,-last_modified``.
    """

    def reversed(way: int, value: Any) -> str:
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


def records_equal(a: dict, b: dict) -> bool:
    """
    Compare records attributes, ignoring those assigned automatically
    by the server.
    """
    ignore_fields = ("last_modified", "schema")
    ac = {k: v for k, v in a.items() if k not in ignore_fields}
    bc = {k: v for k, v in b.items() if k not in ignore_fields}
    return ac == bc


def collection_diff(
    src: Iterable[dict], dest: Iterable[dict]
) -> Tuple[List[dict], List[Tuple[dict, dict]], List[dict]]:
    """
    Compare two lists of records.
    """
    dest_by_id = {r["id"]: r for r in dest}
    to_create: List[dict] = []
    to_update: List[Tuple[dict, dict]] = []
    for r in src:
        record = dest_by_id.pop(r["id"], None)
        if record is None:
            to_create.append(r)
        elif not records_equal(r, record):
            r.pop("last_modified", None)
            to_update.append((record, r))
    to_delete = list(dest_by_id.values())
    return to_create, to_update, to_delete


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of specified file."""
    with open(filepath, "rb") as f:
        binary = f.read()
    h = hashlib.sha256(binary)
    return h.hexdigest()

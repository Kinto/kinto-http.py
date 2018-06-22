import functools
import json
import re
import unicodedata
from datetime import date, datetime
from unidecode import unidecode


VALID_SLUG_REGEXP = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')


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
        value = value.decode('ascii')  # pragma: nocover
    value = unicodedata.normalize('NFKD', value).lower()
    value = re.sub('[^\w\s-]', '', value.lower()).strip()
    value = re.sub('[-\s]+', '-', value)
    return value


def urljoin(server_url, path):
    """Return the url concatenation of server_url and path."""
    return server_url.rstrip('/') + '/' + path.lstrip('/')


def quote(text):
    if hasattr(text, 'strip'):
        text = text.strip('"')
    return '"{0}"'.format(text)


def chunks(l, n):
    """Yield successive n-sized chunks from l.
    Source: http://stackoverflow.com/a/312464
    """
    if n > 0:
        for i in range(0, len(l), n):
            yield l[i:i+n]
    else:
        yield l


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s is not serializable" % type(obj))


json_dumps = functools.partial(json.dumps, default=json_serial)

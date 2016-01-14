import re
import unicodedata
from unidecode import unidecode
import six

REGEXP = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')


def slugify(value):
    """Normalizes string, converts to lowercase, removes non-alpha characters
    and converts spaces to hyphens.
    """
    value = six.text_type(value)
    # Do not lowercase already valid value.
    if REGEXP.match(value):
        return value

    value = unidecode(value)
    if isinstance(value, six.binary_type):
        value = value.decode('ascii')  # pragma: nocover
    value = unicodedata.normalize('NFKD', value).lower()
    value = re.sub('[^\w\s-]', '', value.lower()).strip()
    value = re.sub('[-\s]+', '-', value)
    return value


def urljoin(server_url, path):
    """Return the url concatenation of server_url and path."""
    return server_url.rstrip('/') + '/' + path.lstrip('/')


def quote(text):
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

import re
import unicodedata
from unidecode import unidecode
import six


def slugify(value):
    """Normalizes string, converts to lowercase, removes non-alpha characters
    and converts spaces to hyphens.
    """
    value = unidecode(value)
    if isinstance(value, six.binary_type):
        value = value.decode('ascii')
    value = unicodedata.normalize('NFKD', value).lower()
    value = re.sub('[^\w\s-]', '', value.lower()).strip()
    value = re.sub('[-\s]+', '-', value)
    return value

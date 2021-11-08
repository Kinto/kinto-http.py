import logging

from kinto_http import utils
from kinto_http.exceptions import KintoException


logger = logging.getLogger(__name__)


class Endpoints(object):
    endpoints = {
        "root": "{root}/",
        "batch": "{root}/batch",
        "buckets": "{root}/buckets",
        "bucket": "{root}/buckets/{bucket}",
        "history": "{root}/buckets/{bucket}/history",
        "groups": "{root}/buckets/{bucket}/groups",
        "group": "{root}/buckets/{bucket}/groups/{group}",
        "collections": "{root}/buckets/{bucket}/collections",
        "collection": "{root}/buckets/{bucket}/collections/{collection}",
        "records": "{root}/buckets/{bucket}/collections/{collection}/records",  # NOQA
        "record": "{root}/buckets/{bucket}/collections/{collection}/records/{id}",  # NOQA
    }

    def __init__(self, root=""):
        self._root = root

    def get(self, endpoint, **kwargs):
        # Remove nullable values from the kwargs, and slugify the values.
        kwargs = dict((k, utils.slugify(v)) for k, v in kwargs.items() if v)

        try:
            pattern = self.endpoints[endpoint]
            return pattern.format(root=self._root, **kwargs)
        except KeyError as e:
            msg = "Cannot get {endpoint} endpoint, {field} is missing"
            raise KintoException(msg.format(endpoint=endpoint, field=",".join(e.args)))

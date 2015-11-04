import requests
import json
# import six
# import uuid

from kinto_client import utils
from kinto_client.batch import batch_requests  # noqa
from kinto_client.exceptions import BucketNotFound, KintoException


__all__ = ('Endpoints', 'Session', 'Client', 'batch_requests',
           'create_session', 'BucketNotFound', 'KintoException')


OBJECTS_PERMISSIONS = {
    'bucket': ['group:create', 'collection:create', 'write', 'read'],
    'group': ['write', 'read'],
    'collection': ['write', 'read', 'record:create'],
    'record': ['read', 'write']
}

ID_FIELD = 'id'


def create_session(server_url=None, auth=None, session=None):
    """Returns a session from the passed arguments.

    :param server_url:
        The url of the server to use, with the prefix.
    :param auth:
        A requests authentication policy object.
    :param session:
        An optional session object to use, rather than creating a new one.
    """
    # XXX Refactor the create_session to take place in the caller objects.
    # E.g. test if the session exists before calling create_session.
    if session is not None and (
            server_url is not None or auth is not None):
        msg = ("You cannot specify session and server_url or auth. "
               "Chose either session or (auth + server_url).")
        raise AttributeError(msg)
    if session is None and server_url is None and auth is None:
        msg = ("You need to either set session or auth + server_url")
        raise AttributeError(msg)
    if session is None:
        session = Session(server_url=server_url, auth=auth)
    return session


class Endpoints(object):
    endpoints = {
        'root':         '{root}/',
        'batch':        '{root}/batch',
        'buckets':      '{root}/buckets',
        'bucket':       '{root}/buckets/{bucket}',
        'collections':  '{root}/buckets/{bucket}/collections',
        'collection':   '{root}/buckets/{bucket}/collections/{collection}',
        'records':      '{root}/buckets/{bucket}/collections/{collection}/records',      # NOQA
        'record':       '{root}/buckets/{bucket}/collections/{collection}/records/{id}'  # NOQA
    }

    def __init__(self, root=''):
        self._root = root

    def get(self, endpoint, **kwargs):
        # Remove nullable values from the kwargs.
        kwargs = dict((k, v) for k, v in kwargs.iteritems() if v)

        try:
            return self.endpoints[endpoint].format(root=self._root, **kwargs)
        except KeyError as e:
            msg = "Cannot get {endpoint} endpoint, {field} is missing"
            raise KeyError(msg.format(endpoint=endpoint, field=','.join(e.args)))


class Session(object):
    """Handles all the interactions with the network.
    """
    def __init__(self, server_url, auth=None):
        self.server_url = server_url
        self.auth = auth

    def request(self, method, url, data=None, permissions=None, **kwargs):
        actual_url = utils.urljoin(self.server_url, url)
        if self.auth is not None:
            kwargs.setdefault('auth', self.auth)

        payload = {}
        # if data is not None:
        payload['data'] = data or {}
        if permissions is not None:
            if hasattr(permissions, 'as_dict'):
                permissions = permissions.as_dict()
            payload['permissions'] = permissions
        if payload:
            kwargs.setdefault('headers', {})\
                  .setdefault('Content-Type', 'application/json')
            kwargs.setdefault('data', json.dumps(payload))
        resp = requests.request(method, actual_url, **kwargs)
        if not (200 <= resp.status_code < 400):
            exception = KintoException(resp.status_code)
            exception.request = resp.request
            exception.response = resp
            raise exception

        # XXX Add the status code.
        return resp.json(), resp.headers


class Client(object):

    def __init__(self, server_url=None, session=None, auth=None,
                 bucket=None, collection=None):
        self.session = create_session(server_url, auth, session)
        self._bucket_name = bucket
        self._collection_name = collection
        self.endpoints = Endpoints()
        self.update_bucket = self.create_bucket  # Alias.

    def _get_endpoint(self, name, bucket=None, collection=None, id=None):
        kwargs = {
            'bucket': bucket or self._bucket_name,
            'collection': collection or self._collection_name,
            'id': id
        }
        return self.endpoints.get(name, **kwargs)

    def create_bucket(self, bucket=None):
        endpoint = self._get_endpoint('bucket', bucket)
        return self.session.request('put', endpoint)

    def delete_bucket(self, bucket=None):
        endpoint = self._get_endpoint('bucket', bucket)
        return self.session.request('delete', endpoint)

    def get_collections(self, bucket=None):
        endpoint = self._get_endpoint('collections', bucket)
        return self.session.request('get', endpoint)

    def create_collection(self, collection=None, bucket=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        # XXX Add permissions
        return self.session.request('put', endpoint)

    def get_collection(self, collection=None, bucket=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        return self.session.request('get', endpoint)

    def delete_collection(self, collection=None, bucket=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        resp, _ = self.session.request('delete', endpoint)
        return resp['data']

    def get_records(self, collection=None, bucket=None):
        """Returns all the records"""
        # XXX Add filter and sorting.
        # XXX Add support for pagination.
        endpoint = self._get_endpoint('records', bucket, collection)
        resp, _ = self.session.request('get', endpoint)
        return resp['data']

    def get_record(self, id, collection=None, bucket=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        return self.session.request('get', endpoint)

    def create_record(self, data, collection=None, bucket=None):
        # XXX Add permissions support
        endpoint = self._get_endpoint('records', bucket, collection)
        return self.session.request('post', endpoint, data=data)

    def update_record(self, record, collection=None, bucket=None):
        # XXX How should we deal with permissions? Should a dict with the
        # data and permissions keys be passed?
        endpoint = self._get_endpoint('record', bucket, collection,
                                      record['id'])
        return self.session.request('put', endpoint, data=record)

    def delete_record(self, id, collection=None, bucket=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        resp, _ = self.session.request('delete', endpoint)
        return resp['data']

    def delete_records(self, records):
        # XXX To be done with a BATCH operation
        pass

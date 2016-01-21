import collections
import requests
import uuid
from six import iteritems
from six.moves.urllib.parse import urlparse

from contextlib import contextmanager


from kinto_client import utils
from kinto_client import batch
from kinto_client.exceptions import BucketNotFound, KintoException


__all__ = ('Endpoints', 'Session', 'Client',
           'create_session', 'BucketNotFound', 'KintoException')


OBJECTS_PERMISSIONS = {
    'bucket': ['group:create', 'collection:create', 'write', 'read'],
    'group': ['write', 'read'],
    'collection': ['write', 'read', 'record:create'],
    'record': ['read', 'write']
}

ID_FIELD = 'id'
DO_NOT_OVERWRITE = {'If-None-Match': '*'}


def create_session(server_url=None, auth=None, session=None):
    """Returns a session from the passed arguments.

    :param server_url:
        The URL of the server to use, with the prefix.
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
        # Remove nullable values from the kwargs, and slugify the values.
        kwargs = dict((k, utils.slugify(v))
                      for k, v in iteritems(kwargs) if v)

        try:
            pattern = self.endpoints[endpoint]
            return pattern.format(root=self._root, **kwargs)
        except KeyError as e:
            msg = "Cannot get {endpoint} endpoint, {field} is missing"
            raise KintoException(msg.format(endpoint=endpoint,
                                 field=','.join(e.args)))


class Session(object):
    """Handles all the interactions with the network.
    """
    def __init__(self, server_url, auth=None):
        self.server_url = server_url
        self.auth = auth

    def request(self, method, endpoint, data=None, permissions=None,
                payload=None, **kwargs):
        parsed = urlparse(endpoint)
        if not parsed.scheme:
            actual_url = utils.urljoin(self.server_url, endpoint)
        else:
            actual_url = endpoint

        if self.auth is not None:
            kwargs.setdefault('auth', self.auth)

        payload = payload or {}
        # if data is not None:
        payload['data'] = data or {}
        if permissions is not None:
            if hasattr(permissions, 'as_dict'):
                permissions = permissions.as_dict()
            payload['permissions'] = permissions
        if payload:
            payload_kwarg = 'data' if 'files' in kwargs else 'json'
            kwargs.setdefault(payload_kwarg, payload)
        resp = requests.request(method, actual_url, **kwargs)
        if not (200 <= resp.status_code < 400):
            message = '{0} - {1}'.format(resp.status_code, resp.json())
            exception = KintoException(message)
            exception.request = resp.request
            exception.response = resp
            raise exception

        # XXX Add the status code.
        return resp.json(), resp.headers


class Client(object):

    def __init__(self, server_url=None, session=None, auth=None,
                 bucket=None, collection=None):
        self.endpoints = Endpoints()
        self.session = create_session(server_url, auth, session)
        self._bucket_name = bucket
        self._collection_name = collection
        self._server_settings = None

    def clone(self, **kwargs):
        return Client(**{
            'session': kwargs.get('session', self.session),
            'bucket': kwargs.get('bucket', self._bucket_name),
            'collection': kwargs.get('collection', self._collection_name),
        })

    @contextmanager
    def batch(self, **kwargs):
        if self._server_settings is None:
            resp, _ = self.session.request("GET", self._get_endpoint('root'))
            self._server_settings = resp['settings']

        batch_max_requests = self._server_settings['batch_max_requests']
        batch_session = batch.Session(self,
                                      batch_max_requests=batch_max_requests)
        yield self.clone(session=batch_session, **kwargs)
        for (resp, headers) in batch_session.send():
            for i, response in enumerate(resp['responses']):
                status_code = response['status']
                if not (200 <= status_code < 400):
                    message = '{0} - {1}'.format(status_code, response['body'])
                    exception = KintoException(message)
                    exception.request = batch_session.requests[i]
                    exception.response = response
                    raise exception
        batch_session.reset()

    def _get_endpoint(self, name, bucket=None, collection=None, id=None):
        kwargs = {
            'bucket': bucket or self._bucket_name,
            'collection': collection or self._collection_name,
            'id': id
        }
        return self.endpoints.get(name, **kwargs)

    def _paginated(self, endpoint, records=None, visited=None):
        if records is None:
            records = collections.OrderedDict()
        if visited is None:
            visited = set()

        record_resp, headers = self.session.request('get', endpoint)
        records.update(collections.OrderedDict(
            [(r['id'], r) for r in record_resp['data']]))

        visited.add(endpoint)

        if 'next-page' in map(str.lower, headers.keys()):
            # Paginated wants a relative URL, but the returned one is absolute.
            next_page = headers['Next-Page']
            # Due to bug mozilla-services/cliquet#366, check for recursion:
            if next_page not in visited:
                return self._paginated(next_page, records, visited)

        return records.values()

    def _get_cache_headers(self, safe, data=None, last_modified=None):
        has_data = data is not None and data.get('last_modified')

        if (last_modified is None and has_data):
            # Drop the last_modified field since it will be dropped on the
            # server anyway.
            last_modified = data.pop('last_modified')

        if safe and last_modified is not None:
            return {'If-Match': utils.quote(last_modified)}
        # else return None

    # Buckets

    def create_bucket(self, bucket=None, data=None, permissions=None,
                      safe=True):
        headers = DO_NOT_OVERWRITE if safe else None
        endpoint = self._get_endpoint('bucket', bucket)
        resp, _ = self.session.request('put', endpoint,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def update_bucket(self, bucket=None, data=None, permissions=None,
                      safe=True, last_modified=None):
        endpoint = self._get_endpoint('bucket', bucket)
        headers = self._get_cache_headers(safe, data, last_modified)
        resp, _ = self.session.request('patch', endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)

        return resp

    def get_bucket(self, bucket=None):
        endpoint = self._get_endpoint('bucket', bucket)
        try:
            resp, _ = self.session.request('get', endpoint)
        except KintoException as e:
            raise BucketNotFound(bucket or self._bucket_name, e)
        return resp

    def delete_bucket(self, bucket=None, safe=True, last_modified=None):
        endpoint = self._get_endpoint('bucket', bucket)
        headers = self._get_cache_headers(safe, last_modified=last_modified)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        if resp == batch.RESPONSE_BODY:
            return
        return resp['data']

    # Collections

    def get_collections(self, bucket=None):
        endpoint = self._get_endpoint('collections', bucket)
        return self._paginated(endpoint)

    def create_collection(self, collection=None, bucket=None,
                          data=None, permissions=None, safe=True):
        headers = DO_NOT_OVERWRITE if safe else None
        endpoint = self._get_endpoint('collection', bucket, collection)
        resp, _ = self.session.request('put', endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def update_collection(self, collection=None, bucket=None,
                          data=None, permissions=None, method='put',
                          safe=True, last_modified=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        headers = self._get_cache_headers(safe, data, last_modified)
        resp, _ = self.session.request(method, endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def patch_collection(self, *args, **kwargs):
        kwargs['method'] = 'patch'
        return self.update_collection(*args, **kwargs)

    def get_collection(self, collection=None, bucket=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        resp, _ = self.session.request('get', endpoint)
        return resp

    def delete_collection(self, collection=None, bucket=None,
                          safe=True, last_modified=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        headers = self._get_cache_headers(safe, last_modified=last_modified)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        if resp == batch.RESPONSE_BODY:
            return
        return resp['data']

    # Records

    def get_records(self, collection=None, bucket=None):
        """Returns all the records"""
        # XXX Add filter and sorting.
        endpoint = self._get_endpoint('records', bucket, collection)
        return self._paginated(endpoint)

    def get_record(self, id, collection=None, bucket=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        resp, _ = self.session.request('get', endpoint)
        return resp

    def create_record(self, data, id=None, collection=None, permissions=None,
                      bucket=None, safe=True):
        id = id or data.get('id', None) or str(uuid.uuid4())
        # Make sure that no record already exists with this id.
        headers = DO_NOT_OVERWRITE if safe else None

        endpoint = self._get_endpoint('record', bucket, collection, id)
        resp, _ = self.session.request('put', endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def update_record(self, data, id=None, collection=None, permissions=None,
                      bucket=None, safe=True, method='put',
                      last_modified=None):
        id = id or data.get('id')
        if id is None:
            raise KeyError('Unable to update a record, need an id.')
        endpoint = self._get_endpoint('record', bucket, collection, id)
        headers = self._get_cache_headers(safe, data, last_modified)
        resp, _ = self.session.request(method, endpoint, data=data,
                                       headers=headers,
                                       permissions=permissions)
        return resp

    def patch_record(self, *args, **kwargs):
        kwargs['method'] = 'patch'
        return self.update_record(*args, **kwargs)

    def delete_record(self, id, collection=None, bucket=None,
                      safe=True, last_modified=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        resp, _ = self.session.request(
            'delete', endpoint,
            headers=self._get_cache_headers(safe, last_modified=last_modified))
        if resp == batch.RESPONSE_BODY:
            return
        return resp['data']

    def delete_records(self, records):
        # XXX To be done with a BATCH operation
        pass

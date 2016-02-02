import collections
import uuid
from six import iteritems

from contextlib import contextmanager


from kinto_client import utils
from kinto_client.session import create_session, Session
from kinto_client.batch import Batch
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


class Client(object):

    def __init__(self, server_url=None, session=None, auth=None,
                 bucket="default", collection=None, retry=0, retry_after=None):
        self.endpoints = Endpoints()
        self.session_kwargs = dict(server_url=server_url,
                                   auth=auth,
                                   session=session,
                                   retry=retry,
                                   retry_after=retry_after)
        self.session = create_session(**self.session_kwargs)
        self._bucket_name = bucket
        self._collection_name = collection
        self._server_settings = None

    def clone(self, **kwargs):
        kwargs.setdefault('session', self.session)
        kwargs.setdefault('bucket', self._bucket_name)
        kwargs.setdefault('collection', self._collection_name)
        return Client(**kwargs)

    @contextmanager
    def batch(self, **kwargs):
        if self._server_settings is None:
            resp, _ = self.session.request("GET", self._get_endpoint('root'))
            self._server_settings = resp['settings']

        batch_max_requests = self._server_settings['batch_max_requests']
        batch_session = Batch(self, batch_max_requests=batch_max_requests)
        batch_client = self.clone(session=batch_session, **kwargs)
        yield batch_client
        batch_session.send()
        batch_session.reset()

    def _get_endpoint(self, name, bucket=None, collection=None, id=None):
        kwargs = {
            'bucket': bucket or self._bucket_name,
            'collection': collection or self._collection_name,
            'id': id
        }
        return self.endpoints.get(name, **kwargs)

    def _paginated(self, endpoint, records=None, if_none_match=None, **kwargs):
        if records is None:
            records = collections.OrderedDict()
        headers = {}
        if if_none_match is not None:
            headers['If-None-Match'] = utils.quote(if_none_match)

        record_resp, headers = self.session.request(
            'get', endpoint, headers=headers, params=kwargs)
        if record_resp:
            records_tuples = [(r['id'], r) for r in record_resp['data']]
            records.update(collections.OrderedDict(records_tuples))

            if 'next-page' in map(str.lower, headers.keys()):
                # Paginated wants a relative URL, but the returned one is
                # absolute.
                next_page = headers['Next-Page']
                return self._paginated(next_page, records,
                                       if_none_match=if_none_match)
        return records.values()

    def _get_cache_headers(self, safe, data=None, if_match=None):
        has_data = data is not None and data.get('last_modified')
        if (if_match is None and has_data):
            if_match = data['last_modified']
        if safe and if_match is not None:
            return {'If-Match': utils.quote(if_match)}
        # else return None

    def _create_if_not_exists(self, resource, **kwargs):
        try:
            create_method = getattr(self, 'create_%s' % resource)
            return create_method(**kwargs)
        except KintoException as e:
            if not hasattr(e, 'response') or e.response.status_code != 412:
                raise e
            # The exception contains the existing record in details.existing
            # but it's not enough as we also need to return the permissions.
            get_kwargs = {}
            if resource in('bucket', 'collection', 'record'):
                get_kwargs['bucket'] = kwargs['bucket']
            if resource in ('collection', 'record'):
                get_kwargs['collection'] = kwargs['collection']
            if resource == 'record':
                _id = kwargs.get('id') or kwargs['data']['id']
                get_kwargs['id'] = _id

            get_method = getattr(self, 'get_%s' % resource)
            return get_method(**get_kwargs)

    # Buckets

    def create_bucket(self, bucket=None, data=None, permissions=None,
                      safe=True, if_not_exists=False):
        if if_not_exists:
            return self._create_if_not_exists('bucket',
                                              bucket=bucket,
                                              data=data,
                                              permissions=permissions,
                                              safe=safe)
        headers = DO_NOT_OVERWRITE if safe else None
        endpoint = self._get_endpoint('bucket', bucket)
        resp, _ = self.session.request('put', endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def update_bucket(self, bucket=None, data=None, permissions=None,
                      safe=True, if_match=None, method='put'):
        endpoint = self._get_endpoint('bucket', bucket)
        headers = self._get_cache_headers(safe, data, if_match)
        resp, _ = self.session.request(method, endpoint, data=data,
                                       permissions=permissions,
                                       headers=headers)
        return resp

    def patch_bucket(self, *args, **kwargs):
        kwargs['method'] = 'patch'
        return self.update_bucket(*args, **kwargs)

    def get_buckets(self):
        endpoint = self._get_endpoint('buckets')
        return self._paginated(endpoint)

    def get_bucket(self, bucket=None):
        endpoint = self._get_endpoint('bucket', bucket)
        try:
            resp, _ = self.session.request('get', endpoint)
        except KintoException as e:
            raise BucketNotFound(bucket or self._bucket_name, e)
        return resp

    def delete_bucket(self, bucket=None, safe=True, if_match=None):
        endpoint = self._get_endpoint('bucket', bucket)
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    def delete_buckets(self, safe=True, if_match=None):
        endpoint = self._get_endpoint('buckets')
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    # Collections

    def get_collections(self, bucket=None):
        endpoint = self._get_endpoint('collections', bucket)
        return self._paginated(endpoint)

    def create_collection(self, collection=None, bucket=None,
                          data=None, permissions=None, safe=True,
                          if_not_exists=False):
        if if_not_exists:
            return self._create_if_not_exists('collection',
                                              collection=collection,
                                              bucket=bucket,
                                              data=data,
                                              permissions=permissions,
                                              safe=safe)
        headers = DO_NOT_OVERWRITE if safe else None
        endpoint = self._get_endpoint('collection', bucket, collection)
        try:
            resp, _ = self.session.request('put', endpoint, data=data,
                                           permissions=permissions,
                                           headers=headers)
        except KintoException as e:
            if e.reponse.status_code == 403:
                msg = "Unauthorized. Please check that the bucket exists."
                e.message = msg
            raise e

        return resp

    def update_collection(self, data=None, collection=None, bucket=None,
                          permissions=None, method='put',
                          safe=True, if_match=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        headers = self._get_cache_headers(safe, data, if_match)
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
                          safe=True, if_match=None):
        endpoint = self._get_endpoint('collection', bucket, collection)
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    def delete_collections(self, bucket=None, safe=True, if_match=None):
        endpoint = self._get_endpoint('collections', bucket)
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    # Records

    def get_records(self, collection=None, bucket=None, **kwargs):
        """Returns all the records"""
        # XXX Add filter and sorting.
        endpoint = self._get_endpoint('records', bucket, collection)
        return self._paginated(endpoint, **kwargs)

    def get_record(self, id, collection=None, bucket=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        resp, _ = self.session.request('get', endpoint)
        return resp

    def create_record(self, data, id=None, collection=None, permissions=None,
                      bucket=None, safe=True, if_not_exists=False):
        if if_not_exists:
            return self._create_if_not_exists('record',
                                              data=data,
                                              id=id,
                                              collection=collection,
                                              permissions=permissions,
                                              bucket=bucket,
                                              safe=safe)
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
                      if_match=None):
        id = id or data.get('id')
        if id is None:
            raise KeyError('Unable to update a record, need an id.')
        endpoint = self._get_endpoint('record', bucket, collection, id)
        headers = self._get_cache_headers(safe, data, if_match)
        resp, _ = self.session.request(method, endpoint, data=data,
                                       headers=headers,
                                       permissions=permissions)
        return resp

    def patch_record(self, *args, **kwargs):
        kwargs['method'] = 'patch'
        return self.update_record(*args, **kwargs)

    def delete_record(self, id, collection=None, bucket=None,
                      safe=True, if_match=None):
        endpoint = self._get_endpoint('record', bucket, collection, id)
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    def delete_records(self, collection=None, bucket=None,
                       safe=True, if_match=None):
        endpoint = self._get_endpoint('records', bucket, collection)
        headers = self._get_cache_headers(safe, if_match=if_match)
        resp, _ = self.session.request('delete', endpoint, headers=headers)
        return resp['data']

    def __repr__(self):
        endpoint = self._get_endpoint(
            'collection',
            self._bucket_name,
            self._collection_name
        )
        absolute_endpoint = utils.urljoin(self.session.server_url, endpoint)
        return "<KintoClient %s>" % absolute_endpoint

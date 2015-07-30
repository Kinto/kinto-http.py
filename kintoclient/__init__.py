import requests
import urlparse
import json
import six
import uuid

DEFAULT_SERVER_URL = 'https://kinto.dev.mozaws.net/v1'

OBJECTS_PERMISSIONS = {
    'bucket': ['group:create', 'collection:create', 'write', 'read'],
    'group': ['write', 'read'],
    'collection': ['write', 'read', 'record:create'],
    'record': ['read', 'write']
}

ID_FIELD = 'id'

class KintoException(Exception):
    pass


class BucketNotFound(KintoException):
    pass


def create_session(server_url=None, auth=None, session=None):
    """Returns a session from the passed arguments.

    :param server_url:
        The URL of the server to use, with the prefix.
    :param auth:
        A requests authentication policy object.
    :param session:
        An optional session object to use, rather than creating a new one.
    """
    if session is not None and (
            server_url is not None or auth is not None):
        msg = ("You cannot specify session and server_url or auth. "
               "Chose either session or auth + server_url.")
        raise AttributeError(msg)
    if session is None and server_url is None and auth is None:
        msg = ("You need to either set session or auth + server_url")
        raise AttributeError(msg)
    if session is None:
        session = Session(server_url=server_url, auth=auth)
    return session


class Session(object):
    """Handles all the interactions with the network.
    """
    def __init__(self, server_url=DEFAULT_SERVER_URL, auth=None):
        self.server_url = server_url
        self.auth = auth

    def request(self, method, url, data=None, permissions=None, **kwargs):
        actual_url = urlparse.urljoin(self.server_url, url)
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
        if not 200 <= resp.status_code < 400:
            exception = KintoException(resp.status_code)
            exception.request = resp.request
            exception.response = resp
            raise exception

        return resp.json(), resp.headers


class Permissions(object):
    """Handles the permissions as sets"""
    def __init__(self, object, permissions=None):
        objects = OBJECTS_PERMISSIONS.keys()
        if object not in objects:
            msg = 'object should be one of %s' % ','.join(containers)
            raise AttributeError(msg)

        if permissions is None:
            permissions = {}

        self.object = object
        self.permissions = permissions

        for permission_type in OBJECTS_PERMISSIONS[object]:
            attr = permission_type.replace(':', '_')
            setattr(self, attr, permissions.get(permission_type, []))

    def as_dict(self):
        """Serialize the permissions to be sent to the server"""
        to_save = {}
        for permission_type in OBJECTS_PERMISSIONS[self.object]:
            attr = permission_type.replace(':', '_')
            to_save[permission_type] = list(getattr(self, attr))
        return to_save

    def __repr__(self):
        return "<Permissions on %s: %s>" % (self.object, str(self.permissions))


class Bucket(object):
    """
    All operations are rooted in a bucket. It makes little sense for
    one application to handle multiple buckets at once.
    """

    def __init__(self, name, permissions=None, server_url=None, auth=None,
                 session=None, create=False, load=True):
        """
        :param name:
            The name of the bucket to retrieve.
        :param permissions:
            Permissions to be used when creating a bucket.
        :param server_url:
            The URL of the server to use.
        :param auth:
            A requests authentication policy object.
        :param session:
            An optional session object to use, rather than creating a new one.
        :param create:
            Defines if the bucket should be created. (defaults to False)
        :param load:
            Defines if bucket data should be loaded or not (defaults to True)
        """
        self.session = create_session(server_url, auth, session)
        self.name = name
        self.uri = '/buckets/%s' % self.name
        self.permissions = Permissions(object='bucket')
        self.data = None

        if load:
            # XXX put this logic in a separate method.
            method = 'put' if create and name != 'default' else 'get'

            # In the case of a creation, check if permissions have been passed.
            kwargs = {}
            if method == 'put':
                kwargs['permissions'] = permissions

            try:
                info, _ = self.session.request(method, self.uri, **kwargs)
            except KintoException as e:
                if method == 'get' and e.response.status_code == 403:
                    exception = BucketNotFound(name)
                    exception.response = e.response
                    exception.request = e.request
                    raise exception
                else:
                    raise

            self.data = info['data']
            self.permissions = Permissions(
                object='bucket',
                permissions=info['permissions'])

    def _get_collection_uri(self, collection_id):
        return '%s/collections/%s' % (self.uri, collection_id)

    def get_collection(self, name):
        return Collection(name, bucket=self, session=self.session)

    def list_collections(self):
        uri = "%s/%s" % (self.uri, 'collections')
        resp, _ = self.session.request('get', uri)

        return [collection[ID_FIELD] for collection in resp['data']]

    def create_collection(self, name, permissions=None):
        return Collection(name, bucket=self, session=self.session,
                          create=True, permissions=permissions)

    def delete_collection(self, name):
        uri = self._get_collection_uri(name)
        self.session.request('delete', uri)

    def create_group(self, name, members):
        raise NotImplementedError

    def delete_group(self, name):
        raise NotImplementedError

    def save(self):
        # self.groups.save()
        self.session.request('patch', self.uri, permissions=self.permissions)

    def delete(self):
        self.session.request('delete', self.uri)


class Collection(object):
    """Represents a collection. A collection is a object for records, and
    has attached permissions.
    """
    def __init__(self, name, bucket, permissions=None, server_url=None,
                 auth=None, session=None, create=False, load=True):
        """
        :param name:
            The name of the collection.
        :param server_url:
            The URL of the server to use.
        :param auth:
            A requests authentication policy object.
        :param bucket:
            The bucket object which owns this collection.
        :param session:
            An optional session object to use, rather than creating a new one.
        :param create:
            Defines if the collection should be created. (default to False)
        :param load:
            Defines if collection data should be loaded or not
            (defaults to True)
        """
        self.session = create_session(server_url, auth, session)
        if isinstance(bucket, six.string_types):
            bucket = Bucket(bucket, session=self.session, load=False)
        self.bucket = bucket
        self.name = name
        self.uri = "%s/collections/%s" % (self.bucket.uri, self.name)
        self.permissions = Permissions('collection')
        self.data = None

        if load:
            # XXX put this logic in a separate method.
            method = 'put' if create and self.bucket.name != 'default' else 'get'
            request_kwargs = {}
            if method == 'put' and permissions is not None:
                request_kwargs['permissions'] = permissions

            info, _ = self.session.request(method, self.uri, **request_kwargs)
            self.data = info['data']
            self.permissions = Permissions('collection', info['permissions'])

    def _get_record_uri(self, record_id):
        return '%s/records/%s' % (self.uri, record_id)

    def get_records(self):
        """Returns all the records"""
        # XXX Add filter and sorting.
        records_uri = '%s/records' % self.uri
        resp, _ = self.session.request('get', records_uri)

        # XXX Support permissions for GET /records.
        return [Record(data, collection=self) for data in resp['data']]

    def get_record(self, id):
        record_uri = self._get_record_uri(id)
        resp, _ = self.session.request('get', record_uri)
        return Record(resp['data'],
                      collection=self,
                      permissions=resp['permissions'])

    def save_record(self, record):
        # XXX Rename in update_record and do a PATCH ?
        if record.id is None:
            record.id = str(uuid.uuid4())
        self.session.request('put', self._get_record_uri(record.id),
                             data=record.data, permissions=record.permissions)

    def save_records(self, records):
        # XXX Enhance this with a batch request.
        for record in records:
            self.save_record(record)

    def create_record(self, data, permissions=None, save=True):
        record = Record(data, permissions=permissions, collection=self)
        if save is True:
            self.save_record(record)
        return record

    def delete_record(self, id):
        record_uri = self._get_record_uri(id)
        resp, _ = self.session.request('delete', record_uri)

    def delete_records(self, records):
        # XXX Enhance this with a batch request.
        # with self.session.batch() as batch:
        #     for record in records:
        #         batch.request('delete', self._get_record_uri(record.id))
        for record in records:
            self.delete_record(record.id)

    def delete(self):
        self.session.request('delete', self.uri)


class Record(object):
    """Represents a record"""

    def __init__(self, data, collection, bucket=None, permissions=None,
                 id=None):
        if id is None:
            if ID_FIELD in data:
                id = data[ID_FIELD]
            else:
                # If no id is specified, generate a new one.
                id = str(uuid.uuid4())
        self.id = id
        self.last_modified = data.pop('last_modified', None)
        data.pop(ID_FIELD, None)
        self.collection = collection
        self.permissions = Permissions('record', permissions)
        self.data = data

    def save(self):
        self.collection.save_record(self)

    def delete(self):
        self.collection.delete_record(self.id)

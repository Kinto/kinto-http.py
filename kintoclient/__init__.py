import requests
import urlparse
import json
import six
import uuid

DEFAULT_SERVER_URL = 'https://kinto.dev.mozaws.net/v1'

# XXX rename to 'objects'?
CONTAINER_PERMISSIONS = {
    'bucket': ['group:create', 'collection:create', 'write', 'read'],
    'groups': ['write', 'read'],
    'collections': ['write', 'read', 'record:create'],
    'records': ['read', 'write']
}


def create_session(server_url=None, auth=None, session=None):
    """Returns a session from the passed arguments.

    :param server_url:
        The URL of the server to use.
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

    def request(self, method, url, data=None, **kwargs):
        actual_url = urlparse.urljoin(self.server_url, url)
        if self.auth is not None:
            kwargs.setdefault('auth', self.auth)

        if data is not None:
            kwargs.setdefault('payload', json.dumps(data))
            # XXX Change the Content-Type to JSON.
        resp = requests.request(method, actual_url, **kwargs)
        resp.raise_for_status()
        return resp.json(), resp.headers


class Permissions(object):
    """Handles the permissions as sets"""
    def __init__(self, container, permissions=None):
        containers = CONTAINER_PERMISSIONS.keys()
        if container not in containers:
            msg = 'container should be one of %s' % ','.join(containers)
            raise AttributeError(msg)

        if permissions is None:
            permissions = {}

        self.container = container
        self.permissions = permissions

        for permission_type in CONTAINER_PERMISSIONS[container]:
            attr = permission_type.replace(':', '_')
            setattr(self, attr, set(permissions.get(permission_type, set())))

    def save(self, session):
        to_save = {}
        for permission_type in CONTAINER_PERMISSIONS[self.container]:
            attr = permission_type.replace(':', '_')
            to_save[permission_type] = getattr(self, attr)

        session.request('put', '/%s/permissions' % self.container,
                        data=to_save)


class Bucket(object):
    """
    All operations are rooted in a bucket. It makes little sense for
    one application to handle multiple buckets at once.
    """

    def __init__(self, name, server_url=None, auth=None, session=None,
                 create=False):
        """
        :param name:
            The name of the bucket to retrieve.
        :param server_url:
            The URL of the server to use.
        :param auth:
            A requests authentication policy object.
        :param session:
            An optional session object to use, rather than creating a new one.
        :param create:
            Defines if the bucket should be created. (default to False)
        """
        self.session = create_session(server_url, auth, session)
        self.name = name

        method = 'put' if create and name != 'default' else 'get'
        self.uri = '/buckets/%s' % self.name
        info, _ = self.session.request(method, self.uri)

        self.data = info['data']
        self.permissions = Permissions(
            container='bucket',
            permissions=info.get('permissions'))

    def _get_collection_uri(self, collection_id):
        return '%s/collections/%s' % (self.uri, collection_id)

    def get_collection(self, name):
        return Collection(name, bucket=self, session=self.session)

    def list_collections(self):
        uri = "%s/%s" % (self.uri, 'collections')
        resp, _ = self.session.request('get', uri)

        return [collection['id'] for collection in resp['data']]

    def create_collection(self, name, permissions=None):
        return Collection(name, bucket=self, session=self.session,
                          create=True, permissions=permissions)

    def delete_collection(self, name):
        uri = self._get_collection_uri(name)
        self.session.request('delete', uri)

    def create_group(self, name, members):
        pass

    def delete_group(self, name):
        pass

    def save(self):
        # self.groups.save()
        self.permissions.save()


class Collection(object):
    """Represents a collection. A collection is a container for records, and
    has attached permissions.
    """
    def __init__(self, name, bucket, permissions=None, server_url=None,
                 auth=None, session=None, create=False):
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
        """
        self.session = create_session(server_url, auth, session)
        if isinstance(bucket, six.string_types):
            bucket = Bucket(bucket, session=session)
        self.bucket = bucket
        self.name = name
        self.uri = "%s/collections/%s" % (self.bucket.uri, self.name)

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
        if record.id is None:
            record.id = str(uuid.uuid4())
        self.session.request('put', self._get_record_uri(record.id))

    def save_records(self, records):
        # XXX enhance this with a batch request.
        for record in records:
            self.save_record(record)

    def create_record(self, data, permissions=None, save=True):
        record = Record(data, permissions=permissions, collection=self)
        if save is True:
            self.save_record(record)

    def delete_record(self, id):
        record_uri = self._get_record_uri(id)
        resp, _ = self.session.request('delete', record_uri)

    def delete_records(self, records):
        # XXX TODO
        # with self.session.batch() as batch:
        #     for record in records:
        #         batch.request('delete', self._get_record_uri(record.id))
        pass


class Record(object):
    """Represents a record"""

    def __init__(self, data, collection, permissions=None, id=None):
        if id is None:
            id = str(uuid.uuid4())
        self.id = id
        self.collection = collection
        self.permissions = Permissions('record', permissions)
        self.data = data

    def save(self):
        self.collection.save_record(self)

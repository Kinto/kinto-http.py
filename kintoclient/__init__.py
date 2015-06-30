import requests
import urlparse
import json

DEFAULT_SERVER_URL = 'https://kinto.dev.mozaws.net/v1'

# XXX rename to 'objects'?
CONTAINER_PERMISSIONS = {
    'bucket': ['group:create', 'collection:create', 'write', 'read'],
    'groups': ['write', 'read'],
    'collections': ['write', 'read', 'record:create'],
    'records': ['read', 'write']
}


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
        return resp.json(), resp.headers


class Permissions(object):
    """Handles the permissions as sets"""
    def __init__(self, session, container, permissions=None):
        containers = CONTAINER_PERMISSIONS.keys()
        if container not in containers:
            msg = 'container should be one of %s' % ','.join(containers)
            raise AttributeError(msg)

        if permissions is None:
            permissions = {}

        self.container = container
        self.session = session
        self.permissions = permissions

        for permission_type in CONTAINER_PERMISSIONS[container]:
            attr = permission_type.replace(':', '_')
            setattr(self, attr, set(permissions.get(permission_type, set())))

    def save(self, session=None):
        if session is None:
            session = self.session

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
        :param session:
            An optional session object to use, rather than creating a new one.
        :param server_url:
            The URL of the server to use.
        :param auth:
            A requests authentication policy object.
        :param create:
            Defines if the bucket should be created. (default to False)
        """
        if session is not None and (
                server_url is not None or auth is not None):
            msg = ("You cannot specify session and server_url or auth. "
                   "Chose either session or auth + server_url.")
            raise AttributeError(msg)
        if session is None and server_url is None and auth is None:
            msg = ("You need to either set session or auth + server_url")
            raise AttributeError(msg)

        self.name = name
        if session is None:
            session = Session(server_url=server_url, auth=auth)
        self.session = session

        method = 'put' if create else 'get'
        bucket_uri = '/buckets/%s' % self.name
        info, _ = self.session.request(method, bucket_uri)

        self.data = info['data']
        self.permissions = Permissions(
            session=session,
            container='bucket',
            permissions=info['permissions'])

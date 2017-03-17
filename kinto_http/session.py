import time

import requests
from six.moves.urllib.parse import urlparse

from kinto_http import utils
from kinto_http.exceptions import KintoException, BackoffException


def create_session(server_url=None, auth=None, session=None, retry=0,
                   retry_after=None):
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
        session = Session(server_url=server_url, auth=auth, retry=retry,
                          retry_after=retry_after)
    return session


class Session(object):
    """Handles all the interactions with the network.
    """
    def __init__(self, server_url, auth=None, retry=0, retry_after=None):
        self.server_url = server_url
        self.auth = auth
        self.nb_retry = retry
        self.retry_after = retry_after

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
        if data is not None:
            payload['data'] = data
        if permissions is not None:
            if hasattr(permissions, 'as_dict'):
                permissions = permissions.as_dict()
            payload['permissions'] = permissions
        if method not in ('get', 'head'):
            payload_kwarg = 'data' if 'files' in kwargs else 'json'
            kwargs.setdefault(payload_kwarg, payload)

        retry = self.nb_retry
        while retry >= 0:
            resp = requests.request(method, actual_url, **kwargs)
            retry_after = resp.headers.get("Backoff")
            if retry_after:
                message = '{0} - {1}'.format(resp.status_code, resp.json())
                exception = BackoffException(message, retry_after)
                exception.request = resp.request
                exception.response = resp
                raise exception

            retry = retry - 1
            if not (200 <= resp.status_code < 400):
                if resp.status_code >= 500 and retry >= 0:
                    # Wait and try again.
                    # If not forced, use retry-after header and wait.
                    if self.retry_after is None:
                        retry_after = resp.headers.get("Retry-After", 0)
                    else:
                        retry_after = self.retry_after
                    time.sleep(retry_after)
                    continue

                # Retries exhausted, raise expection.
                message = '{0} - {1}'.format(resp.status_code, resp.json())
                exception = KintoException(message)
                exception.request = resp.request
                exception.response = resp
                raise exception

        if resp.status_code == 304:
            body = None
        else:
            body = resp.json()
        # XXX Add the status code.
        return body, resp.headers

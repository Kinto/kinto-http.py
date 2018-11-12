import json
import pkg_resources
import sys
import time
from urllib.parse import urlparse

import requests

from kinto_http import utils
from kinto_http.exceptions import KintoException, BackoffException


kinto_http_version = pkg_resources.get_distribution("kinto_http").version
requests_version = pkg_resources.get_distribution("requests").version
python_version = '.'.join(map(str, sys.version_info[:3]))

USER_AGENT = 'kinto_http/{} requests/{} python/{}'.format(kinto_http_version,
                                                          requests_version, python_version)


def create_session(server_url=None, auth=None, session=None, **kwargs):
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
        session = Session(server_url=server_url, auth=auth, **kwargs)
    return session


class Session(object):
    """Handles all the interactions with the network.
    """
    def __init__(self, server_url, auth=None, retry=0, retry_after=None):
        self.backoff = None
        self.server_url = server_url
        self.auth = auth
        self.nb_retry = retry
        self.retry_after = retry_after

    def request(self, method, endpoint, data=None, permissions=None,
                payload=None, **kwargs):
        current_time = time.time()
        if self.backoff and self.backoff > current_time:
            seconds = int(self.backoff - current_time)
            raise BackoffException("Retry after {} seconds".format(seconds), seconds)

        parsed = urlparse(endpoint)
        if not parsed.scheme:
            actual_url = utils.urljoin(self.server_url, endpoint)
        else:
            actual_url = endpoint

        if self.auth is not None:
            kwargs.setdefault('auth', self.auth)

        if kwargs.get('headers') is None:
            kwargs['headers'] = dict()

        if kwargs.get('params') is not None:
            params = dict()
            for key, value in kwargs["params"].items():
                if key.startswith('in_') or key.startswith('exclude_'):
                    params[key] = ','.join(value)
                elif isinstance(value, str):
                    params[key] = value
                else:
                    params[key] = json.dumps(value)
            kwargs['params'] = params

        if not isinstance(kwargs['headers'], dict):
            raise TypeError("headers must be a dict (got {})".format(kwargs['headers']))

        # Set the default User-Agent if not already defined.
        # In the meantime, clone the header dict to avoid changing the
        # user header dict when adding information.
        kwargs['headers'] = {"User-Agent": USER_AGENT, **kwargs["headers"]}

        payload = payload or {}
        if data is not None:
            payload['data'] = data
        if permissions is not None:
            if hasattr(permissions, 'as_dict'):
                permissions = permissions.as_dict()
            payload['permissions'] = permissions
        if method not in ('get', 'head'):
            if 'files' in kwargs:
                kwargs.setdefault('data', payload)
            else:
                kwargs.setdefault('data', utils.json_dumps(payload))
                kwargs['headers'].setdefault('Content-Type', 'application/json')

        retry = self.nb_retry
        while retry >= 0:
            resp = requests.request(method, actual_url, **kwargs)
            backoff_seconds = resp.headers.get("Backoff")
            if backoff_seconds:
                self.backoff = time.time() + int(backoff_seconds)
            else:
                self.backoff = None

            retry = retry - 1
            if 200 <= resp.status_code < 400:
                # Success
                break
            else:
                if retry >= 0 and (resp.status_code >= 500 or resp.status_code == 409):
                    # Wait and try again.
                    # If not forced, use retry-after header and wait.
                    if self.retry_after is None:
                        retry_after = int(resp.headers.get("Retry-After", 0))
                    else:
                        retry_after = self.retry_after
                    time.sleep(retry_after)
                    continue

                # Retries exhausted, raise expection.
                try:
                    message = '{0} - {1}'.format(resp.status_code, resp.json())
                except ValueError:
                    # In case the response is not JSON, fallback to text.
                    message = '{0} - {1}'.format(resp.status_code, resp.text)
                exception = KintoException(message)
                exception.request = resp.request
                exception.response = resp
                raise exception
        if resp.status_code == 304 or method == 'head':
            body = None
        else:
            body = resp.json()
        return body, resp.headers

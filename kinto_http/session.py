import json
import time
import warnings
from urllib.parse import urlparse

import requests

import kinto_http
from kinto_http import utils
from kinto_http.constants import USER_AGENT
from kinto_http.exceptions import BackoffException, KintoException


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
    if session is not None and (server_url is not None or auth is not None):
        msg = (
            "You cannot specify session and server_url or auth. "
            "Chose either session or (auth + server_url)."
        )
        raise AttributeError(msg)
    if session is None and server_url is None and auth is None:
        msg = "You need to either set session or auth + server_url"
        raise AttributeError(msg)

    if isinstance(auth, str):
        if ":" in auth:
            auth = tuple(auth.split(":", 1))
        elif "bearer" in auth.lower():
            # eg, "Bearer ghruhgrwyhg"
            _type, token = auth.split(" ", 1)
            auth = kinto_http.BearerTokenAuth(token, type=_type)
        elif auth:  # not empty
            raise ValueError(
                "Unsupported `auth` parameter value. Must be a tuple() or string "
                "in the form of `user:pass` or `Bearer xyz`"
            )

    if session is None:
        session = Session(server_url=server_url, auth=auth, **kwargs)
    return session


class Session(object):
    """Handles all the interactions with the network."""

    def __init__(
        self, server_url, auth=None, timeout=False, headers=None, retry=0, retry_after=None
    ):
        self.backoff = None
        self.server_url = server_url
        self.auth = auth
        self.nb_retry = retry
        self.retry_after = retry_after
        self.timeout = timeout
        self.headers = headers or {}

    def request(self, method, endpoint, data=None, permissions=None, payload=None, **kwargs):
        current_time = time.time()
        if self.backoff and self.backoff > current_time:
            seconds = int(self.backoff - current_time)
            raise BackoffException("Retry after {} seconds".format(seconds), seconds)

        parsed = urlparse(endpoint)
        if not parsed.scheme:
            actual_url = utils.urljoin(self.server_url, endpoint)
        else:
            actual_url = endpoint

        if self.timeout is not False:
            kwargs.setdefault("timeout", self.timeout)

        if self.auth is not None:
            kwargs.setdefault("auth", self.auth)

        if kwargs.get("params") is not None:
            params = dict()
            for key, value in kwargs["params"].items():
                if key.startswith("in_") or key.startswith("exclude_"):
                    params[key] = ",".join(value)
                elif isinstance(value, str):
                    params[key] = value
                else:
                    params[key] = json.dumps(value)
            kwargs["params"] = params

        overridden_headers = kwargs.get("headers") or {}

        # Set the default User-Agent if not already defined.
        kwargs["headers"] = {"User-Agent": USER_AGENT, **self.headers, **overridden_headers}

        payload = payload or {}

        if method.lower() == "get" and (payload or data):
            raise KintoException("GET requests are not allowed to have a body!")

        if data is not None:
            payload["data"] = data

        if permissions is not None:
            if hasattr(permissions, "as_dict"):
                permissions = permissions.as_dict()

            payload["permissions"] = permissions

        if method.lower() not in ("get", "head"):
            if "files" in kwargs:
                kwargs.setdefault("data", payload)

            else:
                kwargs.setdefault("data", utils.json_dumps(payload))
                kwargs["headers"].setdefault("Content-Type", "application/json")

        retry = self.nb_retry
        while retry >= 0:
            resp = requests.request(method, actual_url, **kwargs)

            if "Alert" in resp.headers:
                warnings.warn(resp.headers["Alert"], DeprecationWarning)
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
                    message = "{0} - {1}".format(resp.status_code, resp.json())
                except ValueError:
                    # In case the response is not JSON, fallback to text.
                    message = "{0} - {1}".format(resp.status_code, resp.text)
                exception = KintoException(message)
                exception.request = resp.request
                exception.response = resp
                raise exception
        if resp.status_code == 204 or resp.status_code == 304 or method == "head":
            body = None
        else:
            body = resp.json()
        return body, resp.headers

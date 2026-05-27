import logging
from typing import Optional

import requests
import requests.auth
from requests.models import PreparedRequest

from kinto_http.client import AsyncClient, Client
from kinto_http.endpoints import Endpoints
from kinto_http.exceptions import (
    BucketNotFound,
    CollectionNotFound,
    KintoBatchException,
    KintoException,
)
from kinto_http.login import BrowserOAuth
from kinto_http.session import Session, create_session


logger = logging.getLogger("kinto_http")

__all__ = (
    "BrowserOAuth",
    "TokenAuth",
    "BearerTokenAuth",
    "Endpoints",
    "Session",
    "AsyncClient",
    "Client",
    "create_session",
    "BucketNotFound",
    "CollectionNotFound",
    "KintoException",
    "KintoBatchException",
)


class TokenAuth(requests.auth.AuthBase):
    def __init__(self, token: str, type: Optional[str] = None):
        self.token = token
        self.type = type or "Bearer"

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        # Sets auth-scheme to either Bearer or Basic
        assert r.headers is not None
        r.headers["Authorization"] = "{} {}".format(self.type, self.token)
        return r


class BearerTokenAuth(TokenAuth):
    pass

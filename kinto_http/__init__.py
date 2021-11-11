import logging

import requests

from kinto_http.client import AsyncClient, Client
from kinto_http.endpoints import Endpoints
from kinto_http.exceptions import (
    BucketNotFound,
    CollectionNotFound,
    KintoBatchException,
    KintoException,
)
from kinto_http.session import Session, create_session


logger = logging.getLogger("kinto_http")

__all__ = (
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


class BearerTokenAuth(requests.auth.AuthBase):
    def __init__(self, token, type=None):
        self.token = token
        self.type = type or "Bearer"

    def __call__(self, r):
        r.headers["Authorization"] = "{} {}".format(self.type, self.token)
        return r

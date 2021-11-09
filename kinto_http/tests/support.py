import hashlib
import hmac
from typing import Dict, Tuple
from unittest import mock
from urllib.parse import urljoin

import requests

from kinto_http.constants import DEFAULT_AUTH
from kinto_http.exceptions import KintoException


def mock_response(session, data=None, permissions=None, headers=None, error=False):
    data = data or {}
    permissions = permissions or {}
    headers = headers or {}
    info = {"data": data, "permissions": permissions}
    if error:
        session.request.side_effect = ValueError
    else:
        session.request.return_value = (info, headers)


def get_record(id=None, data=None, permissions=None):
    record = mock.MagicMock()
    record.id = id or "1234"
    record.data = data or {"foo": "bar"}
    record.permissions = permissions or {"read": ["Niko", "Mat"]}
    return record


# Backported from kinto.core.utils
def hmac_digest(secret, message, encoding="utf-8") -> hmac.HMAC:
    """Return hex digest of a message HMAC using secret"""
    if isinstance(secret, str):
        secret = secret.encode(encoding)
    return hmac.new(secret, message.encode(encoding), hashlib.sha256).hexdigest()


def create_user(server_url: str, credentials: Tuple[str, str]) -> Dict:
    account_url = urljoin(server_url, "/accounts/{}".format(credentials[0]))
    r = requests.put(account_url, json={"data": {"password": credentials[1]}}, auth=DEFAULT_AUTH)
    r.raise_for_status()
    return r.json()


def get_user_id(server_url: str, credentials: Tuple[str, str]) -> str:
    r = create_user(server_url, credentials)
    return f"account:{r['data']['id']}"


def build_response(data, headers=None):
    if headers is None:
        headers = {}
    resp = {"data": data}
    return resp, headers


def get_http_error(status):
    exception = KintoException()
    exception.response = mock.MagicMock()
    exception.response.status_code = status
    exception.request = mock.sentinel.request
    return exception


def get_http_response(status, body=None, headers=None):
    if body is None:
        body = mock.sentinel.resp
    if headers is None:
        headers = {}
    resp = mock.MagicMock()
    resp.headers = headers
    resp.status_code = status
    resp.json().return_value = body
    return resp


def get_200():
    return get_http_response(200)


def get_403():
    return get_http_response(403)


def get_503():
    body_503 = {
        "message": "Service temporary unavailable due to overloading",
        "code": 503,
        "error": "Service Unavailable",
        "errno": 201,
    }
    headers_503 = {"Content-Type": "application/json; charset=UTF-8", "Content-Length": 151}
    return get_http_response(503, body=body_503, headers=headers_503)

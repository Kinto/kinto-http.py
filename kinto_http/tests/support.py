from unittest import mock

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

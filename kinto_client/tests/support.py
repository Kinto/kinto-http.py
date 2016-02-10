import unittest2 as unittest  # NOQA

import mock

from kinto_client.exceptions import KintoException


def mock_response(session, data=None, permissions=None, headers=None,
                  error=False):
    data = data or {}
    permissions = permissions or {}
    headers = headers or {}
    info = {'data': data, 'permissions': permissions}
    if error:
        session.request.side_effect = ValueError
    else:
        session.request.return_value = (info, headers)


def get_record(id=None, data=None, permissions=None):
    record = mock.MagicMock()
    record.id = id or '1234'
    record.data = data or {'foo': 'bar'}
    record.permissions = permissions or {'read': ['Niko', 'Mat']}
    return record


def build_response(data, headers=None):
    if headers is None:
        headers = {}
    resp = {
        'data': data
    }
    return resp, headers


def get_http_error(status):
    exception = KintoException()
    exception.response = mock.MagicMock()
    exception.response.status_code = status
    exception.request = mock.sentinel.request
    return exception

def get_200():
    response_200 = mock.MagicMock()
    response_200.status_code = 200
    response_200.json().return_value = mock.sentinel.resp,
    response_200.headers = mock.sentinel.headers
    return response_200

def get_503():
    body_503 = {
        "message": "Service temporary unavailable due to overloading",
        "code": 503,
        "error": "Service Unavailable",
        "errno": 201
    }
    headers_503 = {
        "Content-Type": "application/json; charset=UTF-8",
        "Content-Length": 151
    }
    response_503 = mock.MagicMock()
    response_503.status_code = 503
    response_503.json.return_value = body_503
    response_503.headers = headers_503
    return response_503

def get_403():
    response_403 = mock.MagicMock()
    response_403.status_code = 403
    return response_403

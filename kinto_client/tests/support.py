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

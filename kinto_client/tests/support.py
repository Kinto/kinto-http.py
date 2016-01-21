import unittest2 as unittest  # NOQA

import mock


def mock_response(session, body=None, data=None, permissions=None,
                  headers=None, error=False):
    data = data or {}
    permissions = permissions or {}
    headers = headers or {}
    if body:
        info = body
    else:
        info = {'data': data, 'permissions': permissions}
    if error:
        session.request.side_effect = ValueError
    else:
        session.request.return_value = (info, headers)


def mock_batch(session):
    session.request.side_effect = [
        ({"settings": {"batch_max_requests": 25}}, {}),
        ({"responses": []}, {}),
    ]


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

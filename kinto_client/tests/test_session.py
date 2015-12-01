import mock

from .support import unittest
from kinto_client import (Session, create_session, KintoException)


class SessionTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch('kinto_client.requests')
        self.requests_mock = p.start()
        self.addCleanup(p.stop)

    def test_uses_specified_server_url(self):
        session = Session(mock.sentinel.server_url)
        self.assertEquals(session.server_url, mock.sentinel.server_url)

    def test_no_auth_is_used_by_default(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        self.assertEquals(session.auth, None)
        session.request('get', '/test')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            json={'data': {}})

    def test_bad_http_status_raises_exception(self):
        response = mock.MagicMock()
        response.status_code = 400
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')

        self.assertRaises(KintoException, session.request, 'get', '/test')

    def test_session_injects_auth_on_requests(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session(auth=mock.sentinel.auth,
                          server_url='https://example.org')
        session.request('get', '/test')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            auth=mock.sentinel.auth,
            json={"data": {}})

    def test_requests_arguments_are_forwarded(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', '/test',
                        foo=mock.sentinel.bar)
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            foo=mock.sentinel.bar,
            json={"data": {}})

    def test_passed_data_is_encoded_to_json(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', '/test',
                        data={'foo': 'bar'})
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            json={"data": {'foo': 'bar'}})

    def test_passed_data_is_passed_as_is_when_files_are_posted(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('post', '/test',
                        data='{"foo": "bar"}',
                        files={"attachment": {"filename"}})
        self.requests_mock.request.assert_called_with(
            'post', 'https://example.org/test',
            data={"data": '{"foo": "bar"}'},
            files={"attachment": {"filename"}})

    def test_passed_permissions_is_added_in_the_payload(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        permissions = mock.MagicMock()
        permissions.as_dict.return_value = {'foo': 'bar'}
        session.request('get', '/test',
                        permissions=permissions)
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            json={'data': {}, 'permissions': {'foo': 'bar'}})

    def test_url_is_used_if_schema_is_present(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        permissions = mock.MagicMock()
        permissions.as_dict.return_value = {'foo': 'bar'}
        session.request('get', 'https://example.org/anothertest')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/anothertest',
            json={"data": {}})

    def test_creation_fails_if_session_and_server_url(self):
        self.assertRaises(
            AttributeError, create_session,
            session='test', server_url='http://example.org')
        self.assertRaises(
            AttributeError, create_session,
            'test', session='test', auth=('alexis', 'p4ssw0rd'))

    def test_initialization_fails_on_missing_args(self):
        self.assertRaises(AttributeError, create_session)

    @mock.patch('kinto_client.Session')
    def test_creates_a_session_if_needed(self, session_mock):
        # Mock the session response.
        create_session(server_url=mock.sentinel.server_url,
                       auth=mock.sentinel.auth)
        session_mock.assert_called_with(
            server_url=mock.sentinel.server_url,
            auth=mock.sentinel.auth)

    def test_use_given_session_if_provided(self):
        session = create_session(session=mock.sentinel.session)
        self.assertEquals(session, mock.sentinel.session)

from unittest2 import TestCase
import json
import mock

from kintoclient import Bucket, Session, Permissions, DEFAULT_SERVER_URL


# XXX Put this function in tests/support.py
def mock_response(session, data=None, permissions=None, headers=None):
    data = data or {}
    permissions = permissions or {}
    headers = headers or {}
    info = {'data': data, 'permissions': permissions}
    session.request.return_value = (info, headers)


class BucketTest(TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)

    def test_initialization_fails_if_session_and_server_url(self):
        self.assertRaises(
            AttributeError, Bucket,
            'test', session='test', server_url='http://example.org')
        self.assertRaises(
            AttributeError, Bucket,
            'test', session='test', auth=('alexis', 'p4ssw0rd'))

    def test_initialization_fails_on_missing_args(self):
        self.assertRaises(AttributeError, Bucket, 'test')

    @mock.patch('kintoclient.Session')
    def test_creates_a_session_if_needed(self, session_mock):
        # Mock the session response.
        mock_response(session_mock())
        Bucket('test', server_url=mock.sentinel.server_url,
               auth=mock.sentinel.auth)
        session_mock.assert_called_with(
            server_url=mock.sentinel.server_url,
            auth=mock.sentinel.auth)

    def test_use_given_session_if_provided(self):
        bucket = Bucket('test', session=self.session)
        self.assertEquals(bucket.session, self.session)

    def test_put_is_issued_on_creation(self):
        pass

    def test_get_is_issued_on_retrieval(self):
        pass

    def test_permissions_are_created(self):
        pass


class SessionTest(TestCase):

    def test_default_server_url_used_if_not_provided(self):
        session = Session()
        self.assertEquals(session.server_url, DEFAULT_SERVER_URL)

    def test_uses_specified_server_url(self):
        session = Session(mock.sentinel.server_url)
        self.assertEquals(session.server_url, mock.sentinel.server_url)

    @mock.patch('kintoclient.requests')
    def test_no_auth_is_used_by_default(self, requests_mock):
        session = Session('https://example.org')
        self.assertEquals(session.auth, None)
        session.request('get', 'https://example.org/test')
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test')

    @mock.patch('kintoclient.requests')
    def test_session_injects_auth_on_requests(self, requests_mock):
        session = Session(auth=mock.sentinel.auth,
                          server_url='https://example.org')
        session.request('get', '/test')
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            auth=mock.sentinel.auth)

    @mock.patch('kintoclient.requests')
    def test_requests_arguments_are_forwarded(self, requests_mock):
        session = Session('https://example.org')
        session.request('get', 'https://example.org/test',
                        foo=mock.sentinel.bar)
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            foo=mock.sentinel.bar)

    @mock.patch('kintoclient.requests')
    def test_passed_data_is_encoded_to_json(self, requests_mock):
        session = Session('https://example.org')
        session.request('get', 'https://example.org/test',
                        data={'foo': 'bar'})
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            payload=json.dumps({'foo': 'bar'}))

    def test_passed_data_changes_the_request_content_type(self):
        pass


class PermissionsTests(TestCase):

    def setUp(self):
        self.session = mock.MagicMock()

    def test_should_throw_on_invalid_container(self):
        self.assertRaises(AttributeError, Permissions,
                          self.session, 'unknown_container')

    def test_should_not_throw_on_valid_container(self):
        # Should not raise.
        Permissions(self.session, 'bucket')

    def test_permissions_default_to_empty_dict(self):
        permissions = Permissions(self.session, 'bucket')
        self.assertEquals(permissions.group_create, set())
        self.assertEquals(permissions.collection_create, set())
        self.assertEquals(permissions.write, set())
        self.assertEquals(permissions.read, set())

    def test_permissions_can_be_passed_as_arguments(self):
        permissions = Permissions(
            session=self.session,
            container='bucket',
            permissions={
                'group:create': ['alexis', 'natim'],
                'collection:create': ['mat', 'niko', 'tarek'],
                'read': ['dale', ],
                'write': ['fernando', ]
            })
        self.assertEquals(permissions.group_create, {'alexis', 'natim'})
        self.assertEquals(permissions.collection_create,
                          {'mat', 'niko', 'tarek'})
        self.assertEquals(permissions.write, {'fernando'})
        self.assertEquals(permissions.read, {'dale'})

    def test_can_be_manipulated_as_sets(self):
        Permissions(
            session=self.session,
            container='bucket',
            permissions={
                'group:create': ['alexis', 'natim'],
                'collection:create': ['mat', 'niko', 'tarek'],
                'read': ['dale', ],
                'write': ['fernando', ]
            })
        # XXX work with sets.

    def test_save_issues_a_put(self):
        permissions = {
            'group:create': ['alexis', 'natim'],
        }
        Permissions(
            session=self.session,
            container='bucket',
            permissions=permissions).save()
        # XXX find a way to inspect the content of the request / session.

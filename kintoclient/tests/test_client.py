from unittest2 import TestCase
import json
import mock

from kintoclient import (
    Bucket, Session, Permissions, Collection, Record,
    DEFAULT_SERVER_URL, create_session
)


# XXX Put this function in tests/support.py
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

class BucketTest(TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)

    def test_put_is_issued_on_creation(self):
        Bucket('testbucket', session=self.session, create=True)
        self.session.request.assert_called_with('put', '/buckets/testbucket',
                                                permissions=None)

    def test_get_is_issued_on_retrieval(self):
        Bucket('testbucket', session=self.session)
        self.session.request.assert_called_with('get', '/buckets/testbucket')

    def test_collection_is_not_created_for_personal_bucket(self):
        Bucket('default', session=self.session, create=True)
        self.session.request.assert_called_with('get', '/buckets/default')

    def test_permissions_are_retrieved(self):
        mock_response(self.session, permissions={'read': ['phrawzty', ]})
        bucket = Bucket('testbucket', session=self.session)
        self.assertIn('phrawzty', bucket.permissions.read)

    def test_groups_can_be_created_from_buckets(self):
        pass

    @mock.patch('kintoclient.Collection')
    def test_collections_can_be_retrieved_from_buckets(self, collection_mock):
        bucket = Bucket('testbucket', session=self.session)
        bucket.get_collection('mycollection')
        collection_mock.assert_called_with(
            'mycollection',
            bucket=bucket,
            permissions=None,
            session=self.session)

    @mock.patch('kintoclient.Collection')
    def test_collections_can_be_created_from_buckets(self, collection_mock):
        bucket = Bucket('testbucket', session=self.session)
        bucket.create_collection('mycollection')
        collection_mock.assert_called_with(
            'mycollection',
            bucket=bucket,
            create=True,
            permissions=None,
            session=self.session)

    def test_collections_can_be_deleted_from_buckets(self):
        bucket = Bucket('testbucket', session=self.session)
        bucket.delete_collection('testcollection')
        uri = '/buckets/testbucket/collections/testcollection'
        self.session.request.assert_called_with('delete', uri)

    def test_collections_can_be_retrieved_from_buckets(self):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}])
        bucket = Bucket('testbucket', session=self.session)
        collections = bucket.list_collections()
        self.assertEquals(collections, ['foo', 'bar'])


class SessionTest(TestCase):

    def test_default_server_url_used_if_not_provided(self):
        session = Session()
        self.assertEquals(session.server_url, DEFAULT_SERVER_URL)

    def test_uses_specified_server_url(self):
        session = Session(mock.sentinel.server_url)
        self.assertEquals(session.server_url, mock.sentinel.server_url)

    @mock.patch('kintoclient.requests')
    def test_no_auth_is_used_by_default(self, requests_mock):
        response = mock.MagicMock()
        response.status_code = 200
        requests_mock.request.return_value = response
        session = Session('https://example.org')
        self.assertEquals(session.auth, None)
        session.request('get', 'https://example.org/test')
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            data=json.dumps({'data': {}}),
            headers={'Content-Type': 'application/json'})

    @mock.patch('kintoclient.requests')
    def test_session_injects_auth_on_requests(self, requests_mock):
        response = mock.MagicMock()
        response.status_code = 200
        requests_mock.request.return_value = response
        session = Session(auth=mock.sentinel.auth,
                          server_url='https://example.org')
        session.request('get', '/test')
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            auth=mock.sentinel.auth,
            data='{"data": {}}',
            headers={'Content-Type': 'application/json'})

    @mock.patch('kintoclient.requests')
    def test_requests_arguments_are_forwarded(self, requests_mock):
        response = mock.MagicMock()
        response.status_code = 200
        requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', 'https://example.org/test',
                        foo=mock.sentinel.bar)
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            foo=mock.sentinel.bar,
            data='{"data": {}}',
            headers={'Content-Type': 'application/json'})

    @mock.patch('kintoclient.requests')
    def test_passed_data_is_encoded_to_json(self, requests_mock):
        response = mock.MagicMock()
        response.status_code = 200
        requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', 'https://example.org/test',
                        data={'foo': 'bar'})
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            data=json.dumps({'data': {'foo': 'bar'}}),
            headers={'Content-Type': 'application/json'})

    @mock.patch('kintoclient.requests')
    def test_passed_permissions_is_added_in_the_payload(self, requests_mock):
        response = mock.MagicMock()
        response.status_code = 200
        requests_mock.request.return_value = response
        session = Session('https://example.org')
        permissions = mock.MagicMock()
        permissions.as_dict.return_value = {'foo': 'bar'}
        session.request('get', 'https://example.org/test',
                        permissions=permissions)
        requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            data=json.dumps({'data': {}, 'permissions': {'foo': 'bar'}}),
            headers={'Content-Type': 'application/json'})

    def test_creation_fails_if_session_and_server_url(self):
        self.assertRaises(
            AttributeError, create_session,
            session='test', server_url='http://example.org')
        self.assertRaises(
            AttributeError, create_session,
            'test', session='test', auth=('alexis', 'p4ssw0rd'))

    def test_initialization_fails_on_missing_args(self):
        self.assertRaises(AttributeError, create_session)

    @mock.patch('kintoclient.Session')
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


class PermissionsTests(TestCase):

    def test_fails_with_invalid_object(self):
        self.assertRaises(AttributeError, Permissions, 'unknown_object')

    def test_dont_fail_with_valid_object(self):
        # Should not raise.
        Permissions('bucket')

    def test_permissions_default_to_empty_list(self):
        permissions = Permissions('bucket')
        self.assertEquals(permissions.group_create, [])
        self.assertEquals(permissions.collection_create, [])
        self.assertEquals(permissions.write, [])
        self.assertEquals(permissions.read, [])

    def test_permissions_can_be_passed_as_arguments(self):
        permissions = Permissions(
            object='bucket',
            permissions={
                'group:create': ['alexis', 'natim'],
                'collection:create': ['mat', 'niko', 'tarek'],
                'read': ['dale', ],
                'write': ['fernando', ]
            })
        self.assertEquals(permissions.group_create, ['alexis', 'natim'])
        self.assertEquals(permissions.collection_create,
                          ['mat', 'niko', 'tarek'])
        self.assertEquals(permissions.write, ['fernando', ])
        self.assertEquals(permissions.read, ['dale', ])

    def test_permissions_can_be_manipulated_as_sets(self):
        permissions = Permissions(object='bucket')
        permissions.group_create = set(['mat', ])

        serialized = permissions.as_dict()
        self.assertEquals(serialized['group:create'], ['mat'])

    def test_unknown_permissions_are_ignored(self):
        permissions = Permissions(
            object='bucket',
            permissions={'record:create': ['alexis', 'natim']})
        serialized = permissions.as_dict()
        self.assertNotIn('record:create', serialized)

    def test_dict_serialization(self):
        permissions = {
            'group:create': ['alexis', 'natim'],
        }
        session = mock.MagicMock()
        perm = Permissions(object='bucket', permissions=permissions)
        serialized = perm.as_dict()
        self.assertDictEqual(serialized, {
            'collection:create': [],
            'group:create': ['alexis', 'natim'],
            'read': [],
            'write': [],
        })


class GroupTest(TestCase):

    def test_group_can_be_saved(self):
        pass

    def test_group_issues_a_get_on_retrieval(self):
        pass

    def test_groups_can_be_manipulated_as_lists(self):
        pass

    def test_groups_can_be_cleared(self):
        pass


class CollectionTest(TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)
        self.bucket = mock.MagicMock()
        self.bucket.uri = '/buckets/mybucket'

    def test_collection_can_be_instanciated(self):
        Collection('mycollection', bucket=self.bucket, session=self.session)

    def test_collection_retrieval_issues_an_http_get(self):
        Collection('mycollection', bucket=self.bucket, session=self.session)
        uri = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with('get', uri)

    def test_collection_creation_issues_an_http_put(self):
        Collection('mycollection', bucket=self.bucket, session=self.session,
                   permissions=mock.sentinel.permissions, create=True)
        uri = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', uri, permissions=mock.sentinel.permissions)

    @mock.patch('kintoclient.Bucket')
    def test_bucket_can_be_passed_as_a_string(self, bucket_mock):
        Collection('mycollection', bucket='default', session=self.session)
        bucket_mock.assert_called_with('default', session=self.session,
                                       load=False)

    @mock.patch('kintoclient.Record')
    def test_collection_can_create_records(self, record_mock):
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        collection.create_record(
            {'foo': 'bar'},
            permissions=mock.sentinel.permissions)
        record_mock.assert_called_with(
            data={'foo': 'bar'},
            permissions=mock.sentinel.permissions,
            collection=collection,
            create=True,
            session=self.session)

    @mock.patch('kintoclient.Record')
    def test_create_record_can_save(self, record_mock):
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        record = collection.create_record(
            {'foo': 'bar'},
            permissions=mock.sentinel.permissions)
        record_mock.assert_called_with(
            collection=collection, create=True, data={'foo': 'bar'},
            permissions=mock.sentinel.permissions, session=self.session
        )

    @mock.patch('kintoclient.Record')
    def test_collection_can_retrieve_all_records(self, record_mock):
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}])
        records = collection.get_records()
        self.assertEquals(len(records), 2)
        kwargs = dict(collection=collection, session=self.session)
        record_mock.assert_any_call(data={'id': 'foo'}, **kwargs)
        record_mock.assert_any_call(data={'id': 'bar'}, **kwargs)

    def test_collection_can_save_a_list_records(self):
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        records = [mock.MagicMock(), mock.MagicMock()]
        collection.save_records(records)

        for record in records:
            record.save.assert_called_with()

    def test_collection_can_delete_a_record(self):
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        collection.delete_record(id=1234)
        uri = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', uri)

    def test_collection_can_delete_a_list_of_records(self):
        records = [get_record(id=i) for i in range(1, 10)]
        collection = Collection('mycollection', bucket=self.bucket,
                                session=self.session)
        collection.delete_records(records)
        uri = '/buckets/mybucket/collections/mycollection/records/9'
        self.session.request.assert_any_call('delete', uri)
        self.assertEquals(self.session.request.call_count, 10)


class RecordTest(TestCase):
    def setUp(self):
        self.collection = mock.MagicMock()
        self.collection.uri = "/collection"
        self.session = mock.MagicMock()

    def test_record_id_is_created_if_not_given(self):
        record = Record({'foo': 'bar'}, collection=self.collection,
                        session=self.session, load=False)
        self.assertIsNotNone(record.id)

    def test_generated_record_id_is_an_uuid(self):
        record = Record({'foo': 'bar'}, collection=self.collection,
                        session=self.session, load=False)

        uuid_regexp = r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}'
        self.assertRegexpMatches(record.id, uuid_regexp)

    @mock.patch('kintoclient.Permissions')
    def test_records_handles_permissions(self, permissions_mock):
        record = Record({'foo': 'bar'}, collection=self.collection,
                        permissions=mock.sentinel.permissions,
                        session=self.session, load=False)
        permissions_mock.assert_called_with('record', mock.sentinel.permissions)

    def test_records_save_issues_a_request(self):
        mock_response(self.session)
        record = Record({'foo': 'bar'}, id='1234', collection=self.collection,
                        session=self.session, load=False)
        record.save()
        self.session.request.assert_called_with(
            'put',
            '/collection/records/1234',
            data={'foo': 'bar'},
            permissions=record.permissions)

    # @mock.patch('kintoclient.Record')
    # def test_collection_can_retrieve_a_specific_record(self, record_mock):
    #     data = {'id': '1234', 'foo': 'bar'}
    #     permissions = {'read': ['Natim', 'Mat']}
    #     mock_response(self.session, data=data, permissions=permissions)
    #     collection = Collection('mycollection', bucket=self.bucket,
    #                             session=self.session)
    #     collection.get_record('1234')
    #     uri = '/buckets/mybucket/collections/mycollection/records/1234'
    #     self.session.request.assert_called_with('get', uri)
    #     record_mock.assert_called_with(data, collection=collection,
    #                                    permissions=permissions)

    # def test_collection_can_save_a_record(self):
    #     collection = Collection('mycollection', bucket=self.bucket,
    #                             session=self.session)
    #     record = get_record()
    #     collection.save_record(record)
    #     uri = '/buckets/mybucket/collections/mycollection/records/1234'
    #     self.session.request.assert_called_with('put', uri, data=record.data,
    #                                             permissions=record.permissions)

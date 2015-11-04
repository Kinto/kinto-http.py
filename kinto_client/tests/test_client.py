import mock

from .support import unittest, mock_response

from kinto_client import KintoException, BucketNotFound, Client


class BucketTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_put_is_issued_on_creation(self):
        self.client.create_bucket('testbucket')
        self.session.request.assert_called_with('put', '/buckets/testbucket',
                                                permissions=None)

    def test_get_is_issued_on_retrieval(self):
        self.client.get_bucket('testbucket')
        self.session.request.assert_called_with('get', '/buckets/testbucket')

    def test_bucket_names_are_slugified(self):
        self.client.get_bucket('my bucket')
        url = '/buckets/my-bucket'
        self.session.request.assert_called_with('get', url)

    def test_permissions_are_retrieved(self):
        mock_response(self.session, permissions={'read': ['phrawzty', ]})
        bucket = self.client.get_bucket('testbucket')

        self.assertIn('phrawzty', bucket['permissions']['read'])

    def test_unexisting_bucket_raises(self):
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 403
        exception.request = mock.sentinel.request

        self.session.request.side_effect = exception

        with self.assertRaises(BucketNotFound) as cm:
            self.client.get_bucket('test')
        e = cm.exception
        self.assertEquals(e.response, exception.response)
        self.assertEquals(e.request, mock.sentinel.request)
        self.assertEquals(e.message, 'test')

    def test_http_500_raises_an_error(self):
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 400
        exception.request = mock.sentinel.request

        self.session.request.side_effect = exception

        try:
            self.client.get_bucket('test')
        except KintoException as e:
            self.assertEquals(e.response, exception.response)
            self.assertEquals(e.request, mock.sentinel.request)
        else:
            self.fail("Exception not raised")


class CollectionTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)
        self.client = Client(session=self.session, bucket='/bucketname')

    def test_collection_names_are_slugified(self):
        self.client.get_collection('my collection')
        url = '/buckets/mybucket/collections/my-collection'
        self.session.request.assert_called_with('get', url)

    def test_collection_creation_issues_an_http_put(self):
        self.client.create_collection(
            'mycollection',
            permissions=mock.sentinel.permissions, create=True)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, permissions=mock.sentinel.permissions)

    def test_collection_update_issues_an_http_put(self):
        self.client.update_collection(
            'mycollection',
            permissions=mock.sentinel.permissions, create=True)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, permissions=mock.sentinel.permissions)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(
            session=self.session, bucket='bucketname',
            collection='collectionname')

    def test_record_id_is_created_if_not_given(self):
        record = self.client.create_record({'foo': 'bar'})
        assert 'id' in record.keys()

    def test_generated_record_id_is_an_uuid(self):
        record = self.client.create_record({'foo': 'bar'})

        uuid_regexp = r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}'
        self.assertRegexpMatches(record.id, uuid_regexp)

    def test_records_handles_permissions(self):
        self.client.create_record(
            {'id': '1234', 'foo': 'bar'},
            permissions=mock.sentinel.permissions)
        self.session.request.assert_called_with(
            'put',
            '/bucket/bucketname/collection/collectionname/records/1234',
            data={'foo': 'bar'},
            permissions=mock.sentinel.permissions)

    def test_collection_is_resolved_from_it_name(self):
        mock_response(self.session)
        # Specify a different collection name for the client and the operation.
        client = Client(session=self.session, bucket='bucketname',
                        collection='collectionname')
        client.update_record(data={'id': '1234'}, collection='testcollection')

        self.session.request.assert_called_with(
            'put',
            '/bucket/bucketname/collection/testcollection/records/1234',
            data={'id': '1234'},
            permissions=mock.sentinel.permissions)

    def test_record_id_is_derived_from_data_if_present(self):
        mock_response(self.session)
        # Specify a different collection name for the client and the operation.
        client = Client(session=self.session,
                        bucket='bucketname', collection='collectionname')
        client.create_record(data={'id': '1234'})

        self.session.request.assert_called_with(
            'put',
            '/bucket/bucketname/collection/collectionname/records/1234',
            data={'id': '1234'},
            permissions=mock.sentinel.permissions)

    def test_data_and_permissions_are_added_on_create(self):
        mock_response(self.session)
        data = {'foo': 'bar'}
        permissions = {'read': ['mle']}

        self.client.create_record(
            id='1234',
            data=data,
            permissions={'read': ['mle', ]})

        url = '/buckets/default/collections/collectionname/records/1234'
        self.session.request.assert_called_with(
            'put', url, data=data, permissions=permissions)

    def test_records_issues_a_request_on_delete(self):
        mock_response(self.session)
        self.client.delete_record('1234')
        url = '/buckets/default/collections/testcollection/records/1234'
        self.session.request.assert_called_with('delete', url)

    def test_record_issues_a_request_on_retrieval(self):
        mock_response(self.session, data={'foo': 'bar'})
        record = self.client.get_record('1234')

        self.assertEquals(record['data'], {'foo': 'bar'})
        url = '/buckets/default/collections/testcollection/records/1234'
        self.session.request.assert_called_with('get', url)

    def test_collection_can_retrieve_all_records(self, record_mock):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}])
        records = self.client.get_records()
        self.assertEquals(len(records), 2)
        record_mock.assert_any_call(data={'id': 'foo'})
        record_mock.assert_any_call(data={'id': 'bar'})

    def test_collection_can_save_a_list_records(self):
        records = [mock.MagicMock(), mock.MagicMock()]
        self.client.save_records(records)

        # XXX Check that the save is done in a BATCH.

    def test_collection_can_delete_a_record(self):
        self.client.delete_record(id=1234)
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', url)

    def test_collection_can_delete_a_list_of_records(self):
        self.client.delete_records(['1234', '5678'])
        # url = '/buckets/mybucket/collections/mycollection/records/9'
        # XXX check that the delete is done in a BATCH.

    def test_collection_can_be_deleted(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection('collectionname')
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with('delete', url)

import mock
from six import text_type
from .support import unittest, mock_response, build_response, get_http_error

from kinto_client import (KintoException, BucketNotFound, Client,
                          DO_NOT_OVERWRITE)


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_context_manager_works_as_expected(self):
        settings = {"batch_max_requests": 25}
        self.session.request.side_effect = [({"settings": settings}, []),
                                            ({"responses": []}, [])]

        with self.client.batch(bucket='mozilla', collection='test') as batch:
            batch.create_record(id=1234, data={'foo': 'bar'})
            batch.create_record(id=5678, data={'bar': 'baz'})

        self.session.request.assert_called_with(
            'POST',
            '/batch',
            payload={'requests': [
                {'body': {'data': {'foo': 'bar'}},
                 'path': '/buckets/mozilla/collections/test/records/1234',
                 'method': 'PUT',
                 'headers': {'If-None-Match': '*'}},
                {'body': {'data': {'bar': 'baz'}},
                 'path': '/buckets/mozilla/collections/test/records/5678',
                 'method': 'PUT',
                 'headers': {'If-None-Match': '*'}}]})

    def test_batch_raises_exception(self):
        # Make the next call to sess.request raise a 403.
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 403
        exception.request = mock.sentinel.request
        self.session.request.side_effect = exception

        with self.assertRaises(KintoException):
            with self.client.batch(bucket='moz', collection='test') as batch:
                batch.create_record(id=1234, data={'foo': 'bar'})

    def test_batch_raises_exception_if_subrequest_failed(self):
        error = {
            "errno": 121,
            "message": "This user cannot access this resource.",
            "code": 403,
            "error": "Forbidden"
        }
        self.session.request.side_effect = [
            ({"settings": {"batch_max_requests": 25}}, []),
            ({"responses": [
                {"status": 200, "path": "/url1", "body": {}, "headers": {}},
                {"status": 404, "path": "/url2", "body": error, "headers": {}}
            ]}, [])]

        with self.assertRaises(KintoException):
            with self.client.batch(bucket='moz', collection='test') as batch:
                batch.create_record(id=1234, data={'foo': 'bar'})
                batch.create_record(id=5678, data={'tutu': 'toto'})

    def test_client_is_represented_properly(self):
        client = Client(
            server_url="https://kinto.notmyidea.org/v1",
            bucket="homebrewing",
            collection="recipes"
        )
        expected_repr = ("<KintoClient https://kinto.notmyidea.org/v1/"
                         "buckets/homebrewing/collections/recipes>")
        assert str(client) == expected_repr


class BucketTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_put_is_issued_on_creation(self):
        self.client.create_bucket('testbucket')
        self.session.request.assert_called_with(
            'put', '/buckets/testbucket', permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_patch_is_issued_on_update(self):
        self.client.update_bucket(
            'testbucket',
            data={'foo': 'bar', 'last_modified': '1234'},
            permissions={'read': ['natim']})
        self.session.request.assert_called_with(
            'patch',
            '/buckets/testbucket',
            data={'foo': 'bar', 'last_modified': '1234'},
            permissions={'read': ['natim']},
            headers={'If-Match': '"1234"'})

    def test_udpate_bucket_handles_last_modified(self):
        self.client.update_bucket(
            'testbucket',
            data={'foo': 'bar'},
            last_modified=1234)
        self.session.request.assert_called_with(
            'patch',
            '/buckets/testbucket',
            data={'foo': 'bar'},
            permissions=None,
            headers={'If-Match': '"1234"'})

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
        # Make the next call to sess.request raise a 403.
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

    def test_delete_bucket_returns_the_contained_data(self):
        mock_response(self.session, data={'deleted': True})
        assert self.client.delete_bucket('bucket') == {'deleted': True}

    def test_delete_bucket_handles_last_modified(self):
        self.client.delete_bucket('mybucket', last_modified=1234)
        url = '/buckets/mybucket'
        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with('delete', url, headers=headers)

    def test_get_or_create_dont_raise_in_case_of_conflict(self):
        bucket_data = {
            'permissions': mock.sentinel.permissions,
            'data': {'foo': 'bar'}
        }
        self.session.request.side_effect = [
            get_http_error(status=412),
            (bucket_data, None)
        ]
        returned_data = self.client.create_bucket(
            "buck",
            if_not_exists=True)  # Should not raise.
        assert returned_data == bucket_data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_bucket(
                bucket="buck",
                if_not_exists=True)


class CollectionTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)
        self.client = Client(session=self.session, bucket='mybucket')

    def test_collection_names_are_slugified(self):
        self.client.get_collection('my collection')
        url = '/buckets/mybucket/collections/my-collection'
        self.session.request.assert_called_with('get', url)

    def test_collection_creation_issues_an_http_put(self):
        self.client.create_collection(
            'mycollection',
            permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data=None, permissions=mock.sentinel.permissions,
            headers=DO_NOT_OVERWRITE)

    def test_data_can_be_sent_on_creation(self):
        self.client.create_collection(
            'mycollection',
            'testbucket',
            data={'foo': 'bar'})

        self.session.request.assert_called_with(
            'put',
            '/buckets/testbucket/collections/mycollection',
            data={'foo': 'bar'},
            permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_collection_update_issues_an_http_put(self):
        self.client.update_collection(
            'mycollection',
            data={'foo': 'bar'},
            permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar'},
            permissions=mock.sentinel.permissions, headers=None)

    def test_update_handles_last_modified(self):
        self.client.update_collection(
            'mycollection',
            data={'foo': 'bar'},
            last_modified=1234)

        url = '/buckets/mybucket/collections/mycollection'
        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar'},
            headers=headers, permissions=None)

    def test_collection_update_use_an_if_match_header(self):
        data = {'foo': 'bar', 'last_modified': '1234'}
        self.client.update_collection(
            'mycollection',
            data=data,
            permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar', 'last_modified': '1234'},
            permissions=mock.sentinel.permissions,
            headers={'If-Match': '"1234"'})

    def test_patch_collection_issues_an_http_patch(self):
        self.client.patch_collection(
            collection='mycollection',
            data={'key': 'secret'})

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'patch', url, data={'key': 'secret'}, headers=None,
            permissions=None)

    def test_patch_collection_handles_last_modified(self):
        self.client.patch_collection(
            collection='mycollection',
            data={'key': 'secret'},
            last_modified=1234)

        url = '/buckets/mybucket/collections/mycollection'
        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with(
            'patch', url, data={'key': 'secret'}, headers=headers,
            permissions=None)

    def test_get_collections_returns_the_list_of_collections(self):
        mock_response(
            self.session,
            data=[
                {'id': 'foo', 'last_modified': '12345'},
                {'id': 'bar', 'last_modified': '59874'},
            ])

        collections = self.client.get_collections(bucket='default')
        assert list(collections) == [
            {'id': 'foo', 'last_modified': '12345'},
            {'id': 'bar', 'last_modified': '59874'},
        ]

    def test_collection_can_delete_a_list_of_records(self):
        self.client.delete_records(['1234', '5678'])
        # url = '/buckets/mybucket/collections/mycollection/records/9'
        # XXX check that the delete is done in a BATCH.

    def test_collection_can_be_deleted(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection('mycollection')
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_collection_delete_if_match(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection(
            'mycollection',
            last_modified=1234)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'delete', url, headers={'If-Match': '"1234"'})

    def test_collection_delete_if_match_not_included_if_not_safe(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection(
            'mycollection',
            last_modified=1324,
            safe=False)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_get_or_create_doesnt_raise_in_case_of_conflict(self):
        data = {
            'permissions': mock.sentinel.permissions,
            'data': {'foo': 'bar'}
        }
        self.session.request.side_effect = [
            get_http_error(status=412),
            (data, None)
        ]
        returned_data = self.client.create_collection(
            bucket="buck",
            collection="coll",
            if_not_exists=True)  # Should not raise.
        assert returned_data == data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_collection(
                bucket="buck",
                collection="coll",
                if_not_exists=True)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(
            session=self.session, bucket='mybucket',
            collection='mycollection')

    def test_record_id_is_given_after_creation(self):
        mock_response(self.session, data={'id': 5678})
        record = self.client.create_record({'foo': 'bar'})
        assert 'id' in record['data'].keys()

    def test_generated_record_id_is_an_uuid(self):
        mock_response(self.session)
        self.client.create_record({'foo': 'bar'})
        id = self.session.request.mock_calls[0][1][1].split('/')[-1]

        uuid_regexp = r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}'
        self.assertRegexpMatches(id, uuid_regexp)

    def test_records_handles_permissions(self):
        mock_response(self.session)
        self.client.create_record(
            {'id': '1234', 'foo': 'bar'},
            permissions=mock.sentinel.permissions)
        self.session.request.assert_called_with(
            'put',
            '/buckets/mybucket/collections/mycollection/records/1234',
            data={'foo': 'bar', 'id': '1234'},
            permissions=mock.sentinel.permissions,
            headers=DO_NOT_OVERWRITE)

    def test_collection_argument_takes_precedence(self):
        mock_response(self.session)
        # Specify a different collection name for the client and the operation.
        client = Client(session=self.session, bucket='mybucket',
                        collection='wrong_collection')
        client.update_record(data={'id': '1234'}, collection='good_collection',
                             permissions=mock.sentinel.permissions)

        self.session.request.assert_called_with(
            'put',
            '/buckets/mybucket/collections/good_collection/records/1234',
            data={'id': '1234'},
            headers=None,
            permissions=mock.sentinel.permissions)

    def test_record_id_is_derived_from_data_if_present(self):
        mock_response(self.session)
        self.client.create_record(data={'id': '1234', 'foo': 'bar'},
                                  permissions=mock.sentinel.permissions)

        self.session.request.assert_called_with(
            'put',
            '/buckets/mybucket/collections/mycollection/records/1234',
            data={'id': '1234', 'foo': 'bar'},
            permissions=mock.sentinel.permissions,
            headers=DO_NOT_OVERWRITE)

    def test_data_and_permissions_are_added_on_create(self):
        mock_response(self.session)
        data = {'foo': 'bar'}
        permissions = {'read': ['mle']}

        self.client.create_record(
            id='1234',
            data=data,
            permissions=permissions)

        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with(
            'put', url, data=data, permissions=permissions,
            headers=DO_NOT_OVERWRITE)

    def test_creation_sends_if_none_match_by_default(self):
        mock_response(self.session)
        data = {'foo': 'bar'}

        self.client.create_record(
            id='1234',
            data=data)

        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with(
            'put', url, data=data, permissions=None, headers=DO_NOT_OVERWRITE)

    def test_creation_doesnt_add_if_none_match_when_overwrite(self):
        mock_response(self.session)
        data = {'foo': 'bar'}

        self.client.create_record(id='1234', data=data, safe=False)

        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with(
            'put', url, data=data, permissions=None, headers=None)

    def test_records_issues_a_request_on_delete(self):
        mock_response(self.session)
        self.client.delete_record('1234')
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_record_issues_a_request_on_retrieval(self):
        mock_response(self.session, data={'foo': 'bar'})
        record = self.client.get_record('1234')

        self.assertEquals(record['data'], {'foo': 'bar'})
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('get', url)

    def test_collection_can_retrieve_all_records(self):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}])
        records = self.client.get_records()
        assert list(records) == [{'id': 'foo'}, {'id': 'bar'}]

    def test_pagination_is_followed(self):
        # Mock the calls to request.
        link = ('http://example.org/buckets/buck/collections/coll/records/'
                '?token=1234')

        self.session.request.side_effect = [
            # First one returns a list of items with a pagination token.
            build_response(
                [{'id': '1', 'value': 'item1'},
                 {'id': '2', 'value': 'item2'}, ],
                {'Next-Page': link}),
            # Second one returns a list of items without a pagination token.
            build_response(
                [{'id': '3', 'value': 'item3'},
                 {'id': '4', 'value': 'item4'}, ],
            ),
        ]
        records = self.client.get_records('bucket', 'collection')

        assert list(records) == [
            {'id': '1', 'value': 'item1'},
            {'id': '2', 'value': 'item2'},
            {'id': '3', 'value': 'item3'},
            {'id': '4', 'value': 'item4'},
        ]

    def test_pagination_supports_if_none_match(self):
        link = ('http://example.org/buckets/buck/collections/coll/records/'
                '?token=1234')

        self.session.request.side_effect = [
            # First one returns a list of items with a pagination token.
            build_response(
                [{'id': '1', 'value': 'item1'},
                 {'id': '2', 'value': 'item2'}, ],
                {'Next-Page': link}),
            # Second one returns a list of items without a pagination token.
            build_response(
                [{'id': '3', 'value': 'item3'},
                 {'id': '4', 'value': 'item4'}, ],
            ),
        ]
        self.client.get_records('bucket', 'collection',
                                if_none_match="1234")

        # Check that the If-None-Match header is present in the requests.
        self.session.request.assert_any_call(
            'get', '/buckets/collection/collections/bucket/records',
            headers={'If-None-Match': '"1234"'}, params={})
        self.session.request.assert_any_call(
            'get', link, headers={'If-None-Match': '"1234"'}, params={})

    def test_collection_can_delete_a_record(self):
        mock_response(self.session, data={'id': 1234})
        resp = self.client.delete_record(id=1234)
        assert resp == {'id': 1234}
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_collection_can_delete_a_list_of_records(self):
        self.client.delete_records(['1234', '5678'])
        # url = '/buckets/mybucket/collections/mycollection/records/9'
        # XXX check that the delete is done in a BATCH.

    def test_record_delete_if_match(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_record(
            collection='mycollection',
            bucket='mybucket',
            id='1',
            last_modified=1234)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection/records/1'
        self.session.request.assert_called_with(
            'delete', url, headers={'If-Match': '"1234"'})

    def test_record_delete_if_match_not_included_if_not_safe(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_record(
            collection='mycollection',
            bucket='mybucket',
            id='1',
            last_modified=1234,
            safe=False)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection/records/1'
        self.session.request.assert_called_with(
            'delete', url, headers=None)

    def test_update_record_gets_the_id_from_data_if_exists(self):
        mock_response(self.session)
        self.client.update_record(
            bucket='mybucket', collection='mycollection',
            data={'id': 1, 'foo': 'bar'})

        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/collections/mycollection/records/1',
            data={'id': 1, 'foo': 'bar'}, headers=None, permissions=None)

    def test_update_record_handles_last_modified(self):
        mock_response(self.session)
        self.client.update_record(
            bucket='mybucket', collection='mycollection',
            data={'id': 1, 'foo': 'bar'}, last_modified=1234)

        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/collections/mycollection/records/1',
            data={'id': 1, 'foo': 'bar'}, headers=headers, permissions=None)

    def test_patch_record_uses_the_patch_method(self):
        mock_response(self.session)
        self.client.patch_record(
            bucket='mybucket', collection='mycollection',
            data={'id': 1, 'foo': 'bar'})

        self.session.request.assert_called_with(
            'patch', '/buckets/mybucket/collections/mycollection/records/1',
            data={'id': 1, 'foo': 'bar'}, headers=None, permissions=None)

    def test_update_record_raises_if_no_id_is_given(self):
        with self.assertRaises(KeyError) as cm:
            self.client.update_record(
                data={'foo': 'bar'},  # Omit the id on purpose here.
                bucket='mybucket',
                collection='mycollection'
            )
        assert text_type(cm.exception) == (
            "'Unable to update a record, need an id.'")

    def test_get_or_create_doesnt_raise_in_case_of_conflict(self):
        data = {
            'permissions': mock.sentinel.permissions,
            'data': {'foo': 'bar'}
        }
        self.session.request.side_effect = [
            get_http_error(status=412),
            (data, None)
        ]
        returned_data = self.client.create_record(
            bucket="buck",
            collection="coll",
            data={'id': 1234,
                  'foo': 'bar'},
            if_not_exists=True)  # Should not raise.
        assert returned_data == data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_record(
                bucket="buck",
                collection="coll",
                data={'foo': 'bar'},
                if_not_exists=True)

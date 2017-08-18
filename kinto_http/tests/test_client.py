import mock
import pytest
from six import text_type
from .support import unittest, mock_response, build_response, get_http_error
from kinto_http.session import USER_AGENT
from kinto_http import KintoException, BucketNotFound, Client, DO_NOT_OVERWRITE
from kinto_http.session import create_session
from kinto_http.patch_type import MergePatch, JSONPatch


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_server_info(self):
        self.client.server_info()
        self.session.request.assert_called_with('get', '/')

    def test_context_manager_works_as_expected(self):
        settings = {"batch_max_requests": 25}
        self.session.request.side_effect = [({"settings": settings}, []),
                                            ({"responses": []}, [])]

        with self.client.batch(bucket='mozilla', collection='test') as batch:
            batch.create_record(id=1234, data={'foo': 'bar'})
            batch.create_record(id=5678, data={'bar': 'baz'})

        self.session.request.assert_called_with(
            method='POST',
            endpoint='/batch',
            payload={'requests': [
                {'body': {'data': {'foo': 'bar'}},
                 'path': '/buckets/mozilla/collections/test/records/1234',
                 'method': 'PUT',
                 'headers': {'If-None-Match': '*', 'User-Agent': USER_AGENT}},
                {'body': {'data': {'bar': 'baz'}},
                 'path': '/buckets/mozilla/collections/test/records/5678',
                 'method': 'PUT',
                 'headers': {'If-None-Match': '*', 'User-Agent': USER_AGENT}}]})

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

    def test_batch_raises_exception_if_subrequest_failed_with_code_5xx(self):
        error = {
            "errno": 121,
            "message": "This user cannot access this resource.",
            "code": 500,
            "error": "Server Internal Error"
        }
        self.session.request.side_effect = [
            ({"settings": {"batch_max_requests": 25}}, []),
            ({"responses": [
                {"status": 200, "path": "/url1", "body": {}, "headers": {}},
                {"status": 500, "path": "/url2", "body": error, "headers": {}}
            ]}, [])]

        with self.assertRaises(KintoException):
            with self.client.batch(bucket='moz', collection='test') as batch:
                batch.create_record(id=1234, data={'foo': 'bar'})
                batch.create_record(id=5678, data={'tutu': 'toto'})

    def test_batch_dont_raise_exception_if_subrequest_failed_with_code_4xx(self):
        error = {
            "errno": 121,
            "message": "Forbidden",
            "code": 403,
            "error": "This user cannot access this resource."
        }
        self.session.request.side_effect = [
            ({"settings": {"batch_max_requests": 25}}, []),
            ({"responses": [
                {"status": 200, "path": "/url1", "body": {}, "headers": {}},
                {"status": 403, "path": "/url2", "body": error, "headers": {}}
            ]}, [])]

        with self.client.batch(bucket='moz', collection='test') as batch:  # Do not raise
            batch.create_record(id=1234, data={'foo': 'bar'})
            batch.create_record(id=5678, data={'tutu': 'toto'})

    def test_batch_options_are_transmitted(self):
        settings = {"batch_max_requests": 25}
        self.session.request.side_effect = [({"settings": settings}, [])]
        with mock.patch('kinto_http.create_session') as create_session:
            with self.client.batch(bucket='moz', collection='test', retry=12,
                                   retry_after=20):
                _, last_call_kwargs = create_session.call_args_list[-1]
                self.assertEqual(last_call_kwargs['retry'], 12)
                self.assertEqual(last_call_kwargs['retry_after'], 20)

    def test_client_is_represented_properly_with_bucket_and_collection(self):
        client = Client(
            server_url="https://kinto.notmyidea.org/v1",
            bucket="homebrewing",
            collection="recipes"
        )
        expected_repr = ("<KintoClient https://kinto.notmyidea.org/v1/"
                         "buckets/homebrewing/collections/recipes>")
        assert str(client) == expected_repr

    def test_client_is_represented_properly_with_bucket(self):
        client = Client(
            server_url="https://kinto.notmyidea.org/v1",
            bucket="homebrewing",
        )
        expected_repr = ("<KintoClient https://kinto.notmyidea.org/v1/"
                         "buckets/homebrewing>")
        assert str(client) == expected_repr

    def test_client_is_represented_properly_without_bucket(self):
        client = Client(
            server_url="https://kinto.notmyidea.org/v1",
            bucket=None
        )
        expected_repr = ("<KintoClient https://kinto.notmyidea.org/v1/>")
        assert str(client) == expected_repr

    def test_client_uses_default_bucket_if_not_specified(self):
        mock_response(self.session)
        client = Client(session=self.session)
        client.get_bucket()
        self.session.request.assert_called_with('get', '/buckets/default')

    def test_client_uses_passed_bucket_if_specified(self):
        client = Client(
            server_url="https://kinto.notmyidea.org/v1",
            bucket="buck")
        assert client._bucket_name == "buck"

    def test_client_clone_with_auth(self):
        client_clone = self.client.clone(auth=("reviewer", ""))
        assert client_clone.session.auth == ("reviewer", "")
        assert self.client.session != client_clone.session
        assert self.client.session.server_url == client_clone.session.server_url
        assert self.client.session.auth != client_clone.session.auth
        assert self.client.session.nb_retry == client_clone.session.nb_retry
        assert self.client.session.retry_after == client_clone.session.retry_after
        assert self.client._bucket_name == client_clone._bucket_name
        assert self.client._collection_name == client_clone._collection_name

    def test_client_clone_with_server_url(self):
        client_clone = self.client.clone(server_url="https://kinto.notmyidea.org/v1")
        assert client_clone.session.server_url == "https://kinto.notmyidea.org/v1"
        assert self.client.session != client_clone.session
        assert self.client.session.server_url != client_clone.session.server_url
        assert self.client.session.auth == client_clone.session.auth
        assert self.client.session.nb_retry == client_clone.session.nb_retry
        assert self.client.session.retry_after == client_clone.session.retry_after
        assert self.client._bucket_name == client_clone._bucket_name
        assert self.client._collection_name == client_clone._collection_name

    def test_client_clone_with_new_session(self):
        session = create_session(auth=("reviewer", ""),
                                 server_url="https://kinto.notmyidea.org/v1")
        client_clone = self.client.clone(session=session)
        assert client_clone.session == session
        assert self.client.session != client_clone.session
        assert self.client.session.server_url != client_clone.session.server_url
        assert self.client.session.auth != client_clone.session.auth
        assert self.client._bucket_name == client_clone._bucket_name
        assert self.client._collection_name == client_clone._collection_name

    def test_client_clone_with_auth_and_server_url(self):
        client_clone = self.client.clone(auth=("reviewer", ""),
                                         server_url="https://kinto.notmyidea.org/v1")
        assert client_clone.session.auth == ("reviewer", "")
        assert client_clone.session.server_url == "https://kinto.notmyidea.org/v1"
        assert self.client.session != client_clone.session
        assert self.client.session.server_url != client_clone.session.server_url
        assert self.client.session.auth != client_clone.session.auth
        assert self.client.session.nb_retry == client_clone.session.nb_retry
        assert self.client.session.retry_after == client_clone.session.retry_after
        assert self.client._bucket_name == client_clone._bucket_name
        assert self.client._collection_name == client_clone._collection_name

    def test_client_clone_with_existing_session(self):
        client_clone = self.client.clone(session=self.client.session)
        assert self.client.session == client_clone.session
        assert self.client.session.server_url == client_clone.session.server_url
        assert self.client.session.auth == client_clone.session.auth
        assert self.client._bucket_name == client_clone._bucket_name
        assert self.client._collection_name == client_clone._collection_name

    def test_client_clone_with_new_bucket_and_collection(self):
        client_clone = self.client.clone(bucket="bucket_blah", collection="coll_blah")
        assert self.client.session == client_clone.session
        assert self.client.session.server_url == client_clone.session.server_url
        assert self.client.session.auth == client_clone.session.auth
        assert self.client.session.nb_retry == client_clone.session.nb_retry
        assert self.client.session.retry_after == client_clone.session.retry_after
        assert self.client._bucket_name != client_clone._bucket_name
        assert self.client._collection_name != client_clone._collection_name
        assert client_clone._bucket_name == "bucket_blah"
        assert client_clone._collection_name == "coll_blah"

    def test_client_clone_with_auth_and_server_url_bucket_and_collection(self):
        client_clone = self.client.clone(auth=("reviewer", ""),
                                         server_url="https://kinto.notmyidea.org/v1",
                                         bucket="bucket_blah",
                                         collection="coll_blah")
        assert self.client.session != client_clone.session
        assert self.client.session.server_url != client_clone.session.server_url
        assert self.client.session.auth != client_clone.session.auth
        assert self.client._bucket_name != client_clone._bucket_name
        assert self.client._collection_name != client_clone._collection_name
        assert client_clone.session.auth == ("reviewer", "")
        assert client_clone.session.server_url == "https://kinto.notmyidea.org/v1"
        assert client_clone._bucket_name == "bucket_blah"
        assert client_clone._collection_name == "coll_blah"


class BucketTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_put_is_issued_on_creation(self):
        self.client.create_bucket(id='testbucket')
        self.session.request.assert_called_with(
            'put', '/buckets/testbucket', data=None, permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_put_is_issued_on_update(self):
        self.client.update_bucket(id='testbucket',
                                  data={'foo': 'bar', 'last_modified': '1234'},
                                  permissions={'read': ['natim']})
        self.session.request.assert_called_with(
            'put',
            '/buckets/testbucket',
            data={'foo': 'bar', 'last_modified': '1234'},
            permissions={'read': ['natim']},
            headers={'If-Match': '"1234"'})

    def test_patch_is_issued_on_patch(self):
        self.client.create_bucket(id='testbucket')
        self.client.patch_bucket(id='testbucket',
                                 data={'foo': 'bar'},
                                 permissions={'read': ['natim']})
        self.session.request.assert_called_with(
            'patch',
            '/buckets/testbucket',
            payload={'data': {'foo': 'bar'}, 'permissions': {'read': ['natim']}},
            headers={'Content-Type': 'application/json'})

    def test_patch_requires_patch_to_be_patch_type(self):
        with pytest.raises(TypeError):
            self.client.patch_bucket(id='testbucket', changes=5)

    def test_update_bucket_handles_if_match(self):
        self.client.update_bucket(id='testbucket',
                                  data={'foo': 'bar'},
                                  if_match=1234)
        self.session.request.assert_called_with(
            'put',
            '/buckets/testbucket',
            data={'foo': 'bar'},
            permissions=None,
            headers={'If-Match': '"1234"'})

    def test_get_is_issued_on_list_retrieval(self):
        self.client.get_buckets()
        self.session.request.assert_called_with('get', '/buckets',
                                                headers={}, params={})

    def test_get_is_issued_on_retrieval(self):
        self.client.get_bucket(id='testbucket')
        self.session.request.assert_called_with('get', '/buckets/testbucket')

    def test_bucket_names_are_slugified(self):
        self.client.get_bucket(id='my bucket')
        url = '/buckets/my-bucket'
        self.session.request.assert_called_with('get', url)

    def test_permissions_are_retrieved(self):
        mock_response(self.session, permissions={'read': ['phrawzty', ]})
        bucket = self.client.get_bucket(id='testbucket')

        self.assertIn('phrawzty', bucket['permissions']['read'])

    def test_unexisting_bucket_raises(self):
        # Make the next call to sess.request raise a 403.
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 403
        exception.request = mock.sentinel.request
        self.session.request.side_effect = exception

        with self.assertRaises(BucketNotFound) as cm:
            self.client.get_bucket(id='test')
        e = cm.exception
        self.assertEquals(e.response, exception.response)
        self.assertEquals(e.request, mock.sentinel.request)
        self.assertEquals(e.message, 'test')

    def test_unauthorized_raises_a_kinto_exception(self):
        # Make the next call to sess.request raise a 401.
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 401
        exception.request = mock.sentinel.request
        self.session.request.side_effect = exception

        with self.assertRaises(KintoException) as cm:
            self.client.get_bucket(id='test')
        e = cm.exception
        self.assertEquals(e.response, exception.response)
        self.assertEquals(e.request, mock.sentinel.request)
        self.assertEquals(e.message,
                          "Unauthorized. Please authenticate or make sure the bucket "
                          "can be read anonymously.")

    def test_http_500_raises_an_error(self):
        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 400
        exception.request = mock.sentinel.request

        self.session.request.side_effect = exception

        try:
            self.client.get_bucket(id='test')
        except KintoException as e:
            self.assertEquals(e.response, exception.response)
            self.assertEquals(e.request, mock.sentinel.request)
        else:
            self.fail("Exception not raised")

    def test_delete_bucket_returns_the_contained_data(self):
        mock_response(self.session, data={'deleted': True})
        assert self.client.delete_bucket(id='bucket') == {'deleted': True}

    def test_delete_bucket_handles_if_match(self):
        self.client.delete_bucket(id='mybucket', if_match=1234)
        url = '/buckets/mybucket'
        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with('delete', url, headers=headers)

    def test_delete_is_issued_on_list_deletion(self):
        self.client.delete_buckets()
        self.session.request.assert_called_with('delete', '/buckets',
                                                headers=None)

    def test_get_or_create_dont_raise_in_case_of_conflict(self):
        bucket_data = {
            'permissions': mock.sentinel.permissions,
            'data': {'foo': 'bar'}
        }
        self.session.request.side_effect = [
            get_http_error(status=412),
            (bucket_data, None)
        ]
        # Should not raise.
        returned_data = self.client.create_bucket(id="buck", if_not_exists=True)
        assert returned_data == bucket_data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_bucket(id="buck", if_not_exists=True)

    def test_create_bucket_can_deduce_id_from_data(self):
        self.client.create_bucket(data={'id': 'testbucket'})
        self.session.request.assert_called_with(
            'put', '/buckets/testbucket', data={'id': 'testbucket'}, permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_update_bucket_can_deduce_id_from_data(self):
        self.client.update_bucket(data={'id': 'testbucket'})
        self.session.request.assert_called_with(
            'put', '/buckets/testbucket', data={'id': 'testbucket'}, permissions=None,
            headers=None)


class GroupTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)
        self.client = Client(session=self.session, bucket='mybucket')

    def test_create_group_can_deduce_id_from_data(self):
        self.client.create_group(data={'id': 'group'})
        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/groups/group', data={'id': 'group'}, permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_update_group_can_deduce_id_from_data(self):
        self.client.update_group(data={'id': 'group'})
        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/groups/group', data={'id': 'group'}, permissions=None,
            headers=None)

    def test_patch_group_makes_request(self):
        self.client.patch_group(id='group', data={'foo': 'bar'})
        self.session.request.assert_called_with(
            'patch', '/buckets/mybucket/groups/group', payload={'data': {'foo': 'bar'}},
            headers={'Content-Type': 'application/json'})

    def test_patch_requires_patch_to_be_patch_type(self):
        with pytest.raises(TypeError):
            self.client.patch_group(id='testgroup', bucket='testbucket', changes=5)

    def test_create_group_raises_if_group_id_is_missing(self):
        with pytest.raises(KeyError) as e:
            self.client.create_group()
        self.assertEqual('%s' % e.value, "'Please provide a group id'")

    def test_update_group_raises_if_group_id_is_missing(self):
        with pytest.raises(KeyError) as e:
            self.client.update_group()
        self.assertEqual('%s' % e.value, "'Please provide a group id'")


class CollectionTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        mock_response(self.session)
        self.client = Client(session=self.session, bucket='mybucket')

    def test_collection_names_are_slugified(self):
        self.client.get_collection(id='my collection')
        url = '/buckets/mybucket/collections/my-collection'
        self.session.request.assert_called_with('get', url)

    def test_collection_creation_issues_an_http_put(self):
        self.client.create_collection(id='mycollection',
                                      permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data=None, permissions=mock.sentinel.permissions,
            headers=DO_NOT_OVERWRITE)

    def test_data_can_be_sent_on_creation(self):
        self.client.create_collection(id='mycollection',
                                      bucket='testbucket',
                                      data={'foo': 'bar'})

        self.session.request.assert_called_with(
            'put',
            '/buckets/testbucket/collections/mycollection',
            data={'foo': 'bar'},
            permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_collection_update_issues_an_http_put(self):
        self.client.update_collection(id='mycollection',
                                      data={'foo': 'bar'},
                                      permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar'},
            permissions=mock.sentinel.permissions, headers=None)

    def test_update_handles_if_match(self):
        self.client.update_collection(id='mycollection',
                                      data={'foo': 'bar'},
                                      if_match=1234)

        url = '/buckets/mybucket/collections/mycollection'
        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar'},
            headers=headers, permissions=None)

    def test_collection_update_use_an_if_match_header(self):
        data = {'foo': 'bar', 'last_modified': '1234'}
        self.client.update_collection(id='mycollection', data=data,
                                      permissions=mock.sentinel.permissions)

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'put', url, data={'foo': 'bar', 'last_modified': '1234'},
            permissions=mock.sentinel.permissions,
            headers={'If-Match': '"1234"'})

    def test_patch_collection_issues_an_http_patch(self):
        self.client.patch_collection(id='mycollection',
                                     data={'key': 'secret'})

        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'patch', url, payload={'data': {'key': 'secret'}},
            headers={'Content-Type': 'application/json'},
        )

    def test_patch_collection_handles_if_match(self):
        self.client.patch_collection(id='mycollection',
                                     data={'key': 'secret'},
                                     if_match=1234)

        url = '/buckets/mybucket/collections/mycollection'
        headers = {'If-Match': '"1234"', 'Content-Type': 'application/json'}
        self.session.request.assert_called_with(
            'patch', url, payload={'data': {'key': 'secret'}}, headers=headers,
        )

    def test_patch_requires_patch_to_be_patch_type(self):
        with pytest.raises(TypeError):
            self.client.patch_collection(id='testcoll', bucket='testbucket', changes=5)

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

    def test_collection_can_delete_all_its_records(self):
        self.client.delete_records(bucket='abucket', collection='acollection')
        url = '/buckets/abucket/collections/acollection/records'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_delete_is_issued_on_list_deletion(self):
        self.client.delete_collections(bucket='mybucket')
        url = '/buckets/mybucket/collections'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_collection_can_be_deleted(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection(id='mycollection')
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_collection_delete_if_match(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection(id='mycollection', if_match=1234)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection'
        self.session.request.assert_called_with(
            'delete', url, headers={'If-Match': '"1234"'})

    def test_collection_delete_if_match_not_included_if_not_safe(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_collection(id='mycollection',
                                                if_match=1324,
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
        returned_data = self.client.create_collection(bucket="buck",
                                                      id="coll",
                                                      if_not_exists=True)  # Should not raise.
        assert returned_data == data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_collection(bucket="buck",
                                          id="coll",
                                          if_not_exists=True)

    def test_create_collection_raises_a_special_error_on_403(self):
        self.session.request.side_effect = get_http_error(status=403)
        with self.assertRaises(KintoException) as e:
            self.client.create_collection(bucket="buck",
                                          id="coll")
        expected_msg = ("Unauthorized. Please check that the bucket exists "
                        "and that you have the permission to create or write "
                        "on this collection.")
        assert e.exception.message == expected_msg

    def test_create_collection_can_deduce_id_from_data(self):
        self.client.create_collection(data={'id': 'coll'}, bucket='buck')
        self.session.request.assert_called_with(
            'put', '/buckets/buck/collections/coll', data={'id': 'coll'}, permissions=None,
            headers=DO_NOT_OVERWRITE)

    def test_update_collection_can_deduce_id_from_data(self):
        self.client.update_collection(data={'id': 'coll'}, bucket='buck')
        self.session.request.assert_called_with(
            'put', '/buckets/buck/collections/coll', data={'id': 'coll'}, permissions=None,
            headers=None)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.session.request.return_value = (mock.sentinel.response, mock.sentinel.count)
        self.client = Client(
            session=self.session, bucket='mybucket',
            collection='mycollection')

    def test_record_id_is_given_after_creation(self):
        mock_response(self.session, data={'id': 5678})
        record = self.client.create_record(data={'foo': 'bar'})
        assert 'id' in record['data'].keys()

    def test_generated_record_id_is_an_uuid(self):
        mock_response(self.session)
        self.client.create_record(data={'foo': 'bar'})
        id = self.session.request.mock_calls[0][1][1].split('/')[-1]

        uuid_regexp = r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}'
        self.assertRegexpMatches(id, uuid_regexp)

    def test_records_handles_permissions(self):
        mock_response(self.session)
        self.client.create_record(data={'id': '1234', 'foo': 'bar'},
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

        self.client.create_record(id='1234',
                                  data=data,
                                  permissions=permissions)

        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with(
            'put', url, data=data, permissions=permissions,
            headers=DO_NOT_OVERWRITE)

    def test_creation_sends_if_none_match_by_default(self):
        mock_response(self.session)
        data = {'foo': 'bar'}

        self.client.create_record(id='1234', data=data)

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
        self.client.delete_record(id='1234')
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_record_issues_a_request_on_retrieval(self):
        mock_response(self.session, data={'foo': 'bar'})
        record = self.client.get_record(id='1234')

        self.assertEquals(record['data'], {'foo': 'bar'})
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('get', url)

    def test_collection_can_retrieve_all_records(self):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}])
        records = self.client.get_records()
        assert list(records) == [{'id': 'foo'}, {'id': 'bar'}]

    def test_collection_can_retrieve_records_timestamp(self):
        mock_response(self.session, headers={"ETag": '"12345"'})
        timestamp = self.client.get_records_timestamp()
        assert timestamp == '12345'

    def test_records_timestamp_is_cached(self):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}],
                      headers={"ETag": '"12345"'})
        self.client.get_records()
        timestamp = self.client.get_records_timestamp()
        assert timestamp == '12345'
        assert self.session.request.call_count == 1

    def test_records_timestamp_is_cached_per_collection(self):
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}],
                      headers={"ETag": '"12345"'})
        self.client.get_records(collection="foo")
        mock_response(self.session, data=[{'id': 'foo'}, {'id': 'bar'}],
                      headers={"ETag": '"67890"'})
        self.client.get_records(collection="bar")

        timestamp = self.client.get_records_timestamp(collection="foo")
        assert timestamp == '12345'

        timestamp = self.client.get_records_timestamp(collection="bar")
        assert timestamp == '67890'

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
            build_response(
                [{'id': '3', 'value': 'item3'},
                 {'id': '4', 'value': 'item4'}, ],
                {'Next-Page': link}),
            # Second one returns a list of items without a pagination token.
            build_response(
                [{'id': '5', 'value': 'item5'},
                 {'id': '6', 'value': 'item6'}, ],
            ),
        ]
        records = self.client.get_records(bucket='bucket', collection='collection')

        assert list(records) == [
            {'id': '1', 'value': 'item1'},
            {'id': '2', 'value': 'item2'},
            {'id': '3', 'value': 'item3'},
            {'id': '4', 'value': 'item4'},
            {'id': '5', 'value': 'item5'},
            {'id': '6', 'value': 'item6'},
        ]

    def test_pagination_is_followed_for_number_of_pages(self):
        # Mock the calls to request.
        link = ('http://example.org/buckets/buck/collections/coll/records/'
                '?token=1234')

        self.session.request.side_effect = [
            # First one returns a list of items with a pagination token.
            build_response(
                [{'id': '1', 'value': 'item1'},
                 {'id': '2', 'value': 'item2'}, ],
                {'Next-Page': link}),
            build_response(
                [{'id': '3', 'value': 'item3'},
                 {'id': '4', 'value': 'item4'}, ],
                {'Next-Page': link}),
            # Second one returns a list of items without a pagination token.
            build_response(
                [{'id': '5', 'value': 'item5'},
                 {'id': '6', 'value': 'item6'}, ],
            ),
        ]
        records = self.client.get_records(bucket='bucket', collection='collection', pages=2)

        assert list(records) == [
            {'id': '1', 'value': 'item1'},
            {'id': '2', 'value': 'item2'},
            {'id': '3', 'value': 'item3'},
            {'id': '4', 'value': 'item4'},
        ]

    def test_pagination_is_not_followed_if_limit_is_specified(self):
        # Mock the calls to request.
        link = ('http://example.org/buckets/buck/collections/coll/records/'
                '?token=1234')

        self.session.request.side_effect = [
            build_response(
                [{'id': '1', 'value': 'item1'},
                 {'id': '2', 'value': 'item2'}, ],
                {'Next-Page': link}),
            build_response(
                [{'id': '3', 'value': 'item3'},
                 {'id': '4', 'value': 'item4'}, ],
            ),
        ]
        records = self.client.get_records(bucket='bucket', collection='collection', _limit=2)

        assert list(records) == [
            {'id': '1', 'value': 'item1'},
            {'id': '2', 'value': 'item2'}
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
        self.client.get_records(bucket='bucket', collection='collection',
                                if_none_match="1234")

        # Check that the If-None-Match header is present in the requests.
        self.session.request.assert_any_call(
            'get', '/buckets/bucket/collections/collection/records',
            headers={'If-None-Match': '"1234"'}, params={})
        self.session.request.assert_any_call(
            'get', link, headers={'If-None-Match': '"1234"'}, params={})

    def test_collection_can_delete_a_record(self):
        mock_response(self.session, data={'id': 1234})
        resp = self.client.delete_record(id=1234)
        assert resp == {'id': 1234}
        url = '/buckets/mybucket/collections/mycollection/records/1234'
        self.session.request.assert_called_with('delete', url, headers=None)

    def test_record_delete_if_match(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_record(collection='mycollection',
                                            bucket='mybucket',
                                            id='1',
                                            if_match=1234)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection/records/1'
        self.session.request.assert_called_with(
            'delete', url, headers={'If-Match': '"1234"'})

    def test_record_delete_if_match_not_included_if_not_safe(self):
        data = {}
        mock_response(self.session, data=data)
        deleted = self.client.delete_record(collection='mycollection',
                                            bucket='mybucket',
                                            id='1',
                                            if_match=1234,
                                            safe=False)
        assert deleted == data
        url = '/buckets/mybucket/collections/mycollection/records/1'
        self.session.request.assert_called_with(
            'delete', url, headers=None)

    def test_update_record_gets_the_id_from_data_if_exists(self):
        mock_response(self.session)
        self.client.update_record(bucket='mybucket', collection='mycollection',
                                  data={'id': 1, 'foo': 'bar'})

        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/collections/mycollection/records/1',
            data={'id': 1, 'foo': 'bar'}, headers=None, permissions=None)

    def test_update_record_handles_if_match(self):
        mock_response(self.session)
        self.client.update_record(bucket='mybucket', collection='mycollection',
                                  data={'id': 1, 'foo': 'bar'}, if_match=1234)

        headers = {'If-Match': '"1234"'}
        self.session.request.assert_called_with(
            'put', '/buckets/mybucket/collections/mycollection/records/1',
            data={'id': 1, 'foo': 'bar'}, headers=headers, permissions=None)

    def test_patch_record_uses_the_patch_method(self):
        mock_response(self.session)
        self.client.patch_record(bucket='mybucket', collection='mycollection',
                                 data={'id': 1, 'foo': 'bar'})

        self.session.request.assert_called_with(
            'patch', '/buckets/mybucket/collections/mycollection/records/1',
            payload={'data': {'id': 1, 'foo': 'bar'}},
            headers={"Content-Type": "application/json"})

    def test_patch_record_recognizes_patchtype(self):
        mock_response(self.session)
        self.client.patch_record(bucket='mybucket', collection='mycollection',
                                 changes=MergePatch({'foo': 'bar'}), id=1)

        self.session.request.assert_called_with(
            'patch', '/buckets/mybucket/collections/mycollection/records/1',
            payload={'data': {'foo': 'bar'}},
            headers={"Content-Type": "application/merge-patch+json"},
        )

    def test_patch_record_understands_jsonpatch(self):
        mock_response(self.session)
        self.client.patch_record(
            bucket='mybucket', collection='mycollection',
            changes=JSONPatch([{'op': 'add', 'patch': '/baz', 'value': 'qux'}]), id=1)

        self.session.request.assert_called_with(
            'patch', '/buckets/mybucket/collections/mycollection/records/1',
            payload=[{'op': 'add', 'patch': '/baz', 'value': 'qux'}],
            headers={"Content-Type": "application/json-patch+json"},
        )

    def test_patch_record_requires_data_to_be_patch_type(self):
        with pytest.raises(TypeError, match="couldn't understand patch body 5"):
            self.client.patch_record(id=1, collection='testcoll', bucket='testbucket', changes=5)

    def test_patch_record_requires_id(self):
        with pytest.raises(KeyError, match="Unable to patch record, need an id."):
            self.client.patch_record(collection='testcoll', bucket='testbucket', data={})

    def test_update_record_raises_if_no_id_is_given(self):
        with self.assertRaises(KeyError) as cm:
            self.client.update_record(data={'foo': 'bar'},  # Omit the id on purpose here.
                                      bucket='mybucket',
                                      collection='mycollection')
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
        returned_data = self.client.create_record(bucket="buck",
                                                  collection="coll",
                                                  data={'id': 1234,
                                                        'foo': 'bar'},
                                                  if_not_exists=True)  # Should not raise.
        assert returned_data == data

    def test_get_or_create_raise_in_other_cases(self):
        self.session.request.side_effect = get_http_error(status=500)
        with self.assertRaises(KintoException):
            self.client.create_record(bucket="buck",
                                      collection="coll",
                                      data={'foo': 'bar'},
                                      id='record',
                                      if_not_exists=True)

    def test_create_record_raises_a_special_error_on_403(self):
        self.session.request.side_effect = get_http_error(status=403)
        with self.assertRaises(KintoException) as e:
            self.client.create_record(bucket="buck",
                                      collection="coll",
                                      data={'foo': 'bar'})
        expected_msg = ("Unauthorized. Please check that the collection exists"
                        " and that you have the permission to create or write "
                        "on this collection record.")
        assert e.exception.message == expected_msg

    def test_create_record_can_deduce_id_from_data(self):
        self.client.create_record(data={'id': 'record'}, bucket='buck', collection='coll')
        self.session.request.assert_called_with(
            'put', '/buckets/buck/collections/coll/records/record', data={'id': 'record'},
            permissions=None, headers=DO_NOT_OVERWRITE)

    def test_update_record_can_deduce_id_from_data(self):
        self.client.update_record(data={'id': 'record'}, bucket='buck', collection='coll')
        self.session.request.assert_called_with(
            'put', '/buckets/buck/collections/coll/records/record', data={'id': 'record'},
            permissions=None, headers=None)

import unittest
from unittest import mock

from kinto_http.replication import replicate
from kinto_http import Client
from kinto_http import exceptions

from .support import mock_response


class ReplicationTest(unittest.TestCase):

    def setUp(self):
        self.origin = mock.MagicMock()
        self.destination = mock.MagicMock()

    def test_destination_bucket_is_created_if_not_exist(self):
        self.destination.get_bucket.side_effect = exceptions.BucketNotFound
        replicate(self.origin, self.destination)
        self.destination.create_bucket.assert_called_with(if_not_exists=True)

    def test_destination_collection_is_created_if_not_exist(self):
        self.destination.get_collection.side_effect = exceptions.KintoException
        self.origin.get_collection.return_value = {
            'data': mock.sentinel.data,
            'permissions': mock.sentinel.permissions
        }
        replicate(self.origin, self.destination)
        self.destination.create_collection.assert_called_with(
            data=mock.sentinel.data,
            permissions=mock.sentinel.permissions,
            if_not_exists=True
        )

    def test_new_records_are_sent_to_the_destination(self):
        self.origin.get_records.return_value = [
            {'id': '1234', 'foo': 'bar', 'last_modified': 1234},
            {'id': '4567', 'bar': 'baz', 'last_modified': 4567}
        ]
        batch = mock.MagicMock()
        batched = batch().__enter__()
        self.destination.batch = batch

        replicate(self.origin, self.destination)
        batched.update_record.assert_any_call(
            data={'id': '4567', 'bar': 'baz', 'last_modified': 4567},
            safe=False
        )
        batched.update_record.assert_any_call(
            data={'id': '1234', 'foo': 'bar', 'last_modified': 1234},
            safe=False
        )

    def test_removed_records_are_deleted_on_the_destination(self):
        self.origin.get_records.return_value = [
            {'id': '1234', 'deleted': True, 'last_modified': '1234'},
            {'id': '4567', 'deleted': True, 'last_modified': '4567'}
        ]
        batch = mock.MagicMock()
        batched = batch().__enter__()
        self.destination.batch = batch

        replicate(self.origin, self.destination)
        batched.delete_record.assert_any_call('1234', last_modified='1234')
        batched.delete_record.assert_any_call('4567', last_modified='4567')

    @mock.patch('kinto_http.replication.logger')
    def test_logger_outputs_replication_information(self, logger):
        origin_session = mock.MagicMock()
        origin_session.server_url = "http://origin/v1"
        destination_session = mock.MagicMock()
        destination_session.server_url = "http://destination/v1"
        mock_response(origin_session)
        mock_response(destination_session)

        origin = Client(
            session=origin_session,
            bucket="buck",
            collection="coll"
        )
        destination = Client(
            session=destination_session,
            bucket="buck",
            collection="coll"
        )
        destination._server_settings = {'batch_max_requests': 15}
        replicate(origin, destination)
        msg = ("Replication from <KintoClient http://origin/v1/buckets/buck/"
               "collections/coll> to <KintoClient http://destination/v1/"
               "buckets/buck/collections/coll>")
        logger.info.assert_any_call(msg)
        logger.info.assert_any_call("replication of 0 records")

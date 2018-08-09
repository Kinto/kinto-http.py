from .support import unittest

from kinto_http import Endpoints, KintoException


class EndpointsTest(unittest.TestCase):

    def setUp(self):
        self.endpoints = Endpoints()
        self.kwargs = {
            'bucket': 'buck',
            'bucket_id': 5,
            'collection': 'coll',
            'id': 1
        }

    def test_root(self):
        assert self.endpoints.get('root', **self.kwargs) == '/'

    def test_batch(self):
        assert self.endpoints.get('batch', **self.kwargs) == '/batch'

    def test_buckets(self):
        assert self.endpoints.get('buckets', **self.kwargs) == '/buckets'

    def test_bucket(self):
        assert self.endpoints.get('bucket', **self.kwargs) == '/buckets/buck'

    def test_history(self):
        assert self.endpoints.get('history', **self.kwargs) == '/buckets/buck/history'

    def test_collections(self):
        assert self.endpoints.get('collections', **self.kwargs) ==\
            '/buckets/buck/collections'

    def test_collection(self):
        assert self.endpoints.get('collection', **self.kwargs) ==\
            '/buckets/buck/collections/coll'

    def test_records(self):
        assert self.endpoints.get('records', **self.kwargs) ==\
            '/buckets/buck/collections/coll/records'

    def test_record(self):
        assert self.endpoints.get('record', **self.kwargs) ==\
            '/buckets/buck/collections/coll/records/1'

    def test_record_revision(self):
        assert self.endpoints.get('record_revision', history_revision='rev_id', **self.kwargs) ==\
            '/buckets/buck/history?uri=/buckets/buck/collections/coll/records/1'

    def test_missing_arguments_raise_an_error(self):
        # Don't include the record id; it should raise an error.
        with self.assertRaises(KintoException) as context:
            self.endpoints.get('record', bucket='buck',  collection='coll')
        msg = "Cannot get record endpoint, id is missing"
        assert msg in str(context.exception)

    def test_null_arguments_raise_an_error(self):
        # Include a null record id; it should raise an error.
        with self.assertRaises(KintoException) as context:
            self.endpoints.get('record', bucket='buck',  collection='coll',
                               id=None)
        msg = "Cannot get record endpoint, id is missing"
        assert msg in str(context.exception)

    def test_arguments_are_slugified(self):
        assert self.endpoints.get('bucket', bucket='My Bucket') ==\
            "/buckets/my-bucket"

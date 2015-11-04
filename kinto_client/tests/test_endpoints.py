from .support import unittest

from kinto_client import Endpoints


class EndpointsTest(unittest.TestCase):

    def setUp(self):
        self.endpoints = Endpoints()
        self.kwargs = {
            'bucket': 'buck',
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
    

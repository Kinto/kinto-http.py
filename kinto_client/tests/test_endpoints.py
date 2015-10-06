from .support import unittest

from kinto_client import Endpoints


class EndpointsTest(unittest.TestCase):

    def test_endpoints(self):
        endpoints = Endpoints()

        root_endpoint = '/'
        assert endpoints.root() == root_endpoint

        batch_endpoint = '/batch'
        assert endpoints.batch() == batch_endpoint

        buckets_endpoint = '/buckets'
        assert endpoints.buckets() == buckets_endpoint

        bucket_endpoint = '/buckets/buck'
        assert endpoints.bucket('buck') == bucket_endpoint

        collections_endpoint = '/buckets/buck/collections'
        assert endpoints.collections('buck') == collections_endpoint

        collection_endpoint = '/buckets/buck/collections/coll'
        assert endpoints.collection('buck', 'coll') == collection_endpoint

        records_endpoint = '/buckets/buck/collections/coll/records'
        assert endpoints.records('buck', 'coll') == records_endpoint

        record_endpoint = '/buckets/buck/collections/coll/records/1'
        assert endpoints.record('buck', 'coll', '1') == record_endpoint

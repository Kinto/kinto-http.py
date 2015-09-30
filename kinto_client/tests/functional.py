import urlparse
import os.path

import unittest2
import requests
import ConfigParser

from cliquet import utils as cliquet_utils

from kinto_client import Bucket, Collection, Record, BucketNotFound

__HERE__ = os.path.abspath(os.path.dirname(__file__))

SERVER_URL = "http://localhost:8888/v1"
DEFAULT_AUTH = ('user', 'p4ssw0rd')


class FunctionalTest(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(FunctionalTest, self).__init__(*args, **kwargs)
        # XXX Read the configuration from env variables.
        self.server_url = SERVER_URL
        self.auth = DEFAULT_AUTH

        # Read the configuration.
        self.config = ConfigParser.RawConfigParser()
        self.config.read(os.path.join(__HERE__, 'config/kinto.ini'))

    def tearDown(self):
        # Delete all the created objects
        flush_url = urlparse.urljoin(self.server_url, '/__flush__')
        requests.post(flush_url)

    def get_user_id(self, credentials):
        hmac_secret = self.config.get('app:main', 'cliquet.userid_hmac_secret')
        credentials = '%s:%s' % credentials
        digest = cliquet_utils.hmac_digest(hmac_secret, credentials)
        return 'basicauth:%s' % digest

    def create_bucket(self, name='mozilla'):
        bucket = Bucket(name, create=True, server_url=self.server_url,
                        auth=self.auth)
        return bucket

    def create_collection(self, collection_name='payments',
                          bucket_name='mozilla'):
        bucket = self.create_bucket(bucket_name)
        return bucket.create_collection(collection_name)

    def test_bucket_creation(self):
        bucket = Bucket('mozilla', create=True, server_url=self.server_url,
                        auth=self.auth)
        user_id = self.get_user_id(self.auth)
        self.assertIn(user_id, bucket.permissions.write)

    def test_bucket_retrieval(self):
        self.create_bucket()
        Bucket('mozilla', server_url=self.server_url, auth=self.auth)
        # XXX Add permissions handling during creation and check they are
        # present during retrieval.

    def test_bucket_retrieval_fails_when_not_created(self):
        self.assertRaises(BucketNotFound, Bucket,
                          'non-existent', server_url=self.server_url,
                          auth=self.auth)

    def test_bucket_deletion(self):
        bucket = self.create_bucket()
        bucket.delete()
        self.assertRaises(BucketNotFound, Bucket,
                          'mozilla', server_url=self.server_url,
                          auth=self.auth)

    def test_bucket_save(self):
        bucket = self.create_bucket()
        bucket.permissions.write.append("alexis")
        bucket.save()
        bucket = Bucket('mozilla', server_url=self.server_url,
                        auth=self.auth)
        self.assertIn("alexis", bucket.permissions.write)

    def test_collection_creation(self):
        bucket = self.create_bucket()
        bucket.create_collection('payments',
                                 permissions={'write': ['alexis', ]})

        # Test retrieval of a collection gets the permissions as well.
        collection = bucket.get_collection('payments')
        self.assertIn('alexis', collection.permissions.write)

    def test_collection_retrieval(self):
        bucket = self.create_bucket()
        bucket.create_collection('payments')
        collection = bucket.get_collection('payments')
        self.assertEquals(collection.name, 'payments')

    def test_collection_list(self):
        bucket = self.create_bucket()
        for collection in ['receipts', 'assets']:
            collection = bucket.create_collection(collection)

        # The returned collections should be strings.
        collections = bucket.list_collections()
        self.assertEquals(2, len(collections))
        self.assertEquals(set(collections), set(['receipts', 'assets']))

    def test_collection_deletion(self):
        bucket = self.create_bucket()
        collection = bucket.create_collection('payments')
        collection.delete()
        self.assertEquals(len(bucket.list_collections()), 0)

    def test_record_creation_and_retrieval(self):
        collection = self.create_collection('payments')
        created = collection.create_record(
            {'foo': 'bar'},
            permissions={'read': ['alexis']})
        record = collection.get_record(created.id)
        self.assertIn('alexis', record.permissions.read)
        self.assertEquals(record.data, {u'foo': u'bar'})
        self.assertEquals(record.id, created.id)

    def test_single_record_save(self):
        collection = self.create_collection('payments')
        record = collection.create_record(
            {'foo': 'bar'},
            permissions={'read': ['alexis']})
        record.data['bar'] = 'baz'
        record.save()
        retrieved = collection.get_record(record.id)
        self.assertIn('alexis', retrieved.permissions.read)
        self.assertEquals(retrieved.data['foo'], u'bar')
        self.assertEquals(retrieved.data['bar'], u'baz')
        self.assertEquals(record.id, retrieved.id)

    def test_multiple_records_save(self):
        collection = self.create_collection('payments')

        # Create 5 records and retrieve them.
        records = [collection.create_record({'name': i})
                   for i in range(5)]

        # Update their data and save them.
        for r in records:
            r.data['bar'] = 'baz'
        collection.save_records(records)

        # Assert that the change has been submitted.
        retrieved = collection.get_records()
        self.assertTrue(all([r.data['bar'] == 'baz'
                             for r in retrieved]))

    def test_one_record_deletion(self):
        collection = self.create_collection('payments')
        record = collection.create_record({'foo': 'bar'})
        record.delete()

        self.assertEquals(0, len(collection.get_records()))

    def test_multiple_record_deletion(self):
        collection = self.create_collection('payments')
        records = [collection.create_record({'name': i})
                   for i in range(5)]
        collection.delete_records(records)
        self.assertEquals(len(collection.get_records()), 0)

    def test_bucket_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)

        # Create a bucket and share it with alice.
        Bucket('shared-bucket',
               permissions={'read': [alice_userid, ]},
               create=True,
               server_url=self.server_url,
               auth=self.auth)

        # Try to get the bucket as Alice.
        Bucket('shared-bucket',
               server_url=self.server_url,
               auth=alice_credentials)

    def test_collection_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)

        bucket = Bucket('personal-bucket',
                        create=True,
                        server_url=self.server_url,
                        auth=self.auth)

        bucket.create_collection(
            'shared',
            permissions={'read': [alice_userid, ]})

        # Try to read the collection as Alice.
        bucket = Collection('shared', bucket='personal-bucket',
                            server_url=self.server_url,
                            auth=alice_credentials)

    def test_record_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)
        collection = self.create_collection('personal-collection')
        saved = collection.create_record(
            {'foo': 'bar'},
            permissions={'read': [alice_userid, ]})

        # Try to read the record as Alice
        record = Record(
            id=saved.id,
            bucket='mozilla',
            collection='personal-collection',
            server_url=self.server_url,
            auth=alice_credentials)

        self.assertEquals(record.data, {'foo': 'bar'})

if __name__ == '__main__':
    unittest2.main()

import os.path
from six.moves.urllib.parse import urljoin

import unittest2
import requests
from six.moves import configparser

from cliquet import utils as cliquet_utils

from kinto_client import Client, BucketNotFound, KintoException

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
        self.config = configparser.RawConfigParser()
        self.config.read(os.path.join(__HERE__, 'config/kinto.ini'))
        self.client = Client(server_url=self.server_url, auth=self.auth)

    def tearDown(self):
        # Delete all the created objects
        flush_url = urljoin(self.server_url, '/__flush__')
        resp = requests.post(flush_url)
        resp.raise_for_status()

    def get_user_id(self, credentials):
        hmac_secret = self.config.get('app:main', 'cliquet.userid_hmac_secret')
        credentials = '%s:%s' % credentials
        digest = cliquet_utils.hmac_digest(hmac_secret, credentials)
        return 'basicauth:%s' % digest

    def test_bucket_creation(self):
        bucket = self.client.create_bucket('mozilla')
        user_id = self.get_user_id(self.auth)
        assert user_id in bucket['permissions']['write']

    def test_bucket_retrieval(self):
        self.client.create_bucket('mozilla')
        self.client.get_bucket('mozilla')
        # XXX Add permissions handling during creation and check they are
        # present during retrieval.

    def test_bucket_retrieval_fails_when_not_created(self):
        self.assertRaises(BucketNotFound, self.client.get_bucket,
                          'non-existent')

    def test_bucket_deletion(self):
        self.client.create_bucket('mozilla')
        self.client.delete_bucket('mozilla')
        self.assertRaises(BucketNotFound, self.client.get_bucket, 'mozilla')

    def test_bucket_save(self):
        self.client.create_bucket('mozilla', permissions={'write': ['alexis']})
        bucket = self.client.get_bucket('mozilla')
        assert 'alexis' in bucket['permissions']['write']

    def test_collection_creation(self):
        self.client.create_bucket('mozilla')
        self.client.create_collection(
            'payments', bucket='mozilla',
            permissions={'write': ['alexis', ]}
        )

        # Test retrieval of a collection gets the permissions as well.
        collection = self.client.get_collection('payments', bucket='mozilla')
        assert 'alexis' in collection['permissions']['write']

    def test_collection_list(self):
        self.client.create_bucket('mozilla')
        self.client.create_collection('receipts', bucket='mozilla')
        self.client.create_collection('assets', bucket='mozilla')

        # The returned collections should be strings.
        collections = self.client.get_collections('mozilla')
        self.assertEquals(2, len(collections))

        self.assertEquals(set([coll['id'] for coll in collections]),
                          set(['receipts', 'assets']))

    def test_collection_deletion(self):
        self.client.create_bucket('mozilla')
        self.client.create_collection('payments', bucket='mozilla')
        self.client.delete_collection('payments', bucket='mozilla')
        assert len(self.client.get_collections(bucket='mozilla')) == 0

    def test_record_creation_and_retrieval(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        created = client.create_record(data={'foo': 'bar'},
                                       permissions={'read': ['alexis']})
        record = client.get_record(created['data']['id'])
        assert 'alexis' in record['permissions']['read']

    def test_records_list_retrieval(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        client.create_record(data={'foo': 'bar'},
                             permissions={'read': ['alexis']})
        records = client.get_records()
        assert len(records) == 1

    def test_records_paginated_list_retrieval(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        for i in range(10):
            client.create_record(data={'foo': 'bar'},
                                 permissions={'read': ['alexis']})
        # Kinto is running with kinto.paginate_by = 5
        records = client.get_records()
        assert len(records) == 10

    def test_single_record_save(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        created = client.create_record(data={'foo': 'bar'},
                                       permissions={'read': ['alexis']})
        created['data']['bar'] = 'baz'

        # XXX enhance this in order to have to pass only one argument, created.
        client.update_record(id=created['data']['id'], data=created['data'])

        retrieved = client.get_record(created['data']['id'])
        assert 'alexis' in retrieved['permissions']['read']
        assert retrieved['data']['foo'] == u'bar'
        assert retrieved['data']['bar'] == u'baz'
        assert created['data']['id'] == retrieved['data']['id']

    def test_single_record_doesnt_overwrite(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        created = client.create_record(data={'foo': 'bar'},
                                       permissions={'read': ['alexis']})

        with self.assertRaises(KintoException):
            # Create a second record with the ID of the first one.
            client.create_record(data={'id': created['data']['id'],
                                       'bar': 'baz'})

    def test_single_record_can_overwrite(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        created = client.create_record(data={'foo': 'bar'},
                                       permissions={'read': ['alexis']})

        client.create_record(data={'id': created['data']['id'],
                                   'bar': 'baz'}, safe=False)

    def test_one_record_deletion(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()
        record = client.create_record({'foo': 'bar'})
        deleted = client.delete_record(record['data']['id'])
        assert deleted['deleted'] is True
        assert len(client.get_records()) == 0

    def test_bucket_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)

        # Create a bucket and share it with alice.
        self.client.create_bucket('shared-bucket',
                                  permissions={'read': [alice_userid, ]})

        alice_client = Client(server_url=self.server_url,
                              auth=alice_credentials)
        alice_client.get_bucket('shared-bucket')

    def test_updating_data_on_a_collection(self):
        client = Client(server_url=self.server_url, auth=self.auth,
                        bucket='mozilla', collection='payments')
        client.create_bucket()
        client.create_collection()

        client.patch_collection(data={'secret': 'psssssst!'})
        collection = client.get_collection()
        assert collection['data']['secret'] == 'psssssst!'

    def test_collection_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)

        self.client.create_bucket('bob-bucket')
        self.client.create_collection(
            'shared',
            bucket='bob-bucket',
            permissions={'read': [alice_userid, ]})

        # Try to read the collection as Alice.
        alice_client = Client(server_url=self.server_url,
                              auth=alice_credentials)
        alice_client.get_collection('shared', bucket='bob-bucket')

    def test_record_sharing(self):
        alice_credentials = ('alice', 'p4ssw0rd')
        alice_userid = self.get_user_id(alice_credentials)

        # Create a record, and share it with Alice.
        self.client.create_bucket('bob-bucket')
        self.client.create_collection('bob-personal-collection',
                                      bucket='bob-bucket')
        record = self.client.create_record(
            data={'foo': 'bar'},
            permissions={'read': [alice_userid, ]},
            bucket='bob-bucket',
            collection='bob-personal-collection')

        # Try to read the record as Alice
        alice_client = Client(server_url=self.server_url,
                              auth=alice_credentials)
        record = alice_client.get_record(
            id=record['data']['id'],
            bucket='bob-bucket',
            collection='bob-personal-collection')

        assert record['data']['foo'] == 'bar'

    def test_request_batching(self):
        with self.client.batch(bucket='mozilla', collection='fonts') as batch:
            batch.create_bucket()
            batch.create_collection()
            batch.create_record(data={'foo': 'bar'},
                                permissions={'read': ['natim']})
            batch.create_record(data={'bar': 'baz'},
                                permissions={'read': ['alexis']})

        records = self.client.get_records(bucket='mozilla', collection='fonts')
        assert len(records) == 2


if __name__ == '__main__':
    unittest2.main()

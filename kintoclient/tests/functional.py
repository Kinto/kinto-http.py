import unittest2

from kintoclient import Bucket, BucketNotFound

SERVER_URL = "http://localhost:8888/v1"
AUTH = ('user', 'p4ssw0rd')
DEFAULT_USER_ID = ('basicauth:7f1ca4d2d6211a69c6e1d2032545d746371047398b0f1e847'
                   '1bea6eaea1e8091')

class FunctionalTest(unittest2.TestCase):

    def setUp(self):
        # XXX Read the configuration from env variables.
        self.server_url = SERVER_URL
        self.auth = AUTH

    def create_bucket(self):
        bucket = Bucket(
            'mozilla', create=True, server_url=self.server_url,
            auth=AUTH)
        return bucket

    def test_bucket_creation(self):
        bucket = Bucket('mozilla', create=True, server_url=self.server_url,
                        auth=self.auth)
        self.assertIn(DEFAULT_USER_ID, bucket.permissions.write)

    def test_bucket_retrieval(self):
        self.create_bucket()
        bucket = Bucket('mozilla', server_url=self.server_url, auth=self.auth)
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
        pass

    def test_collection_list(self):
        pass

    def test_collection_deletion(self):
        pass

    def test_recod_retrieval(self):
        pass

    def test_record_save(self):
        pass

    def test_records_save(self):
        pass

    def test_one_record_deletion(self):
        pass

    def test_multi_record_deletion(self):
        pass


if __name__ == '__main__':
    unittest2.main()

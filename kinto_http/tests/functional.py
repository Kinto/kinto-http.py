import configparser
import hashlib
import hmac
import os.path
import unittest
from unittest import mock
from urllib.parse import urljoin

import pytest
import requests

from kinto_http import (
    BucketNotFound,
    Client,
    CollectionNotFound,
    KintoException,
    replication,
)
from kinto_http.patch_type import JSONPatch


__HERE__ = os.path.abspath(os.path.dirname(__file__))

SERVER_URL = "http://localhost:8888/v1"
DEFAULT_AUTH = ("user", "p4ssw0rd")


# Backported from kinto.core.utils
def hmac_digest(secret, message, encoding="utf-8"):
    """Return hex digest of a message HMAC using secret"""
    if isinstance(secret, str):
        secret = secret.encode(encoding)
    return hmac.new(secret, message.encode(encoding), hashlib.sha256).hexdigest()


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # XXX Read the configuration from env variables.
        self.server_url = SERVER_URL
        self.auth = DEFAULT_AUTH

        # Read the configuration.
        self.config = configparser.RawConfigParser()
        self.config.read(os.path.join(__HERE__, "config/kinto.ini"))
        self.client = Client(server_url=self.server_url, auth=self.auth)
        self.create_user(self.auth)

    def tearDown(self):
        # Delete all the created objects
        flush_url = urljoin(self.server_url, "/__flush__")
        resp = requests.post(flush_url)
        resp.raise_for_status()

    def create_user(self, credentials):
        account_url = urljoin(self.server_url, "/accounts/{}".format(credentials[0]))
        r = requests.put(
            account_url, json={"data": {"password": credentials[1]}}, auth=DEFAULT_AUTH
        )
        r.raise_for_status()
        return r.json()

    def get_user_id(self, credentials):
        r = self.create_user(credentials)
        return "account:{}".format(r["data"]["id"])

    def test_bucket_creation(self):
        bucket = self.client.create_bucket(id="mozilla")
        user_id = self.get_user_id(self.auth)
        assert user_id in bucket["permissions"]["write"]

    def test_bucket_creation_if_not_exists(self):
        self.client.create_bucket(id="mozilla")
        # Should not raise.
        self.client.create_bucket(id="mozilla", if_not_exists=True)

    def test_buckets_retrieval(self):
        self.client.create_bucket(id="mozilla")
        buckets = self.client.get_buckets()
        assert len(buckets) == 1

    def test_bucket_retrieval(self):
        self.client.create_bucket(id="mozilla")
        self.client.get_bucket(id="mozilla")
        # XXX Add permissions handling during creation and check they are
        # present during retrieval.

    def test_bucket_modification(self):
        bucket = self.client.create_bucket(id="mozilla", data={"version": 1})
        assert bucket["data"]["version"] == 1
        bucket = self.client.patch_bucket(id="mozilla", data={"author": "you"})
        assert bucket["data"]["version"] == 1
        assert bucket["data"]["author"] == "you"
        bucket = self.client.update_bucket(id="mozilla", data={"date": "today"})
        assert bucket["data"]["date"] == "today"
        assert "version" not in bucket["data"]

    def test_bucket_retrieval_fails_when_not_created(self):
        self.assertRaises(BucketNotFound, self.client.get_bucket, id="non-existent")

    def test_bucket_deletion(self):
        self.client.create_bucket(id="mozilla")
        self.client.delete_bucket(id="mozilla")
        self.assertRaises(BucketNotFound, self.client.get_bucket, id="mozilla")

    def test_bucket_deletion_if_exists(self):
        self.client.create_bucket(id="mozilla")
        self.client.delete_bucket(id="mozilla")
        self.client.delete_bucket(id="mozilla", if_exists=True)

    def test_buckets_deletion(self):
        self.client.create_bucket(id="mozilla")
        buckets = self.client.delete_buckets()
        assert buckets[0]["id"] == "mozilla"
        self.assertRaises(BucketNotFound, self.client.get_bucket, id="mozilla")

    def test_buckets_deletion_when_no_buckets_exist(self):
        deleted_buckets = self.client.delete_buckets()
        assert len(deleted_buckets) == 0

    def test_bucket_save(self):
        self.client.create_bucket(id="mozilla", permissions={"write": ["account:alexis"]})
        bucket = self.client.get_bucket(id="mozilla")
        assert "account:alexis" in bucket["permissions"]["write"]

    def test_group_creation(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(
            id="payments",
            bucket="mozilla",
            data={"members": ["blah"]},
            permissions={"write": ["blah"]},
        )
        # Test retrieval of a group gets the permissions as well.
        group = self.client.get_group(id="payments", bucket="mozilla")
        assert "blah" in group["permissions"]["write"]

    def test_group_creation_if_not_exists(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
        self.client.create_group(
            id="payments",
            bucket="mozilla",
            data={"members": ["blah"]},
            permissions={"write": ["blah"]},
            if_not_exists=True,
        )

    def test_group_creation_if_bucket_does_not_exist(self):
        with pytest.raises(KintoException) as e:
            self.client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
        assert str(e.value).endswith(
            "PUT /v1/buckets/mozilla/groups/payments - "
            "403 Unauthorized. Please check that the "
            "bucket exists and that you have the permission "
            "to create or write on this group."
        )

    def test_group_update(self):
        self.client.create_bucket(id="mozilla")
        group = self.client.create_group(
            id="payments", bucket="mozilla", data={"members": ["blah"]}, if_not_exists=True
        )
        assert group["data"]["members"][0] == "blah"
        group = self.client.update_group(
            data={"members": ["blah", "foo"]}, id="payments", bucket="mozilla"
        )
        self.assertEqual(group["data"]["members"][1], "foo")

    def test_group_list(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(id="receipts", bucket="mozilla", data={"members": ["blah"]})
        self.client.create_group(id="assets", bucket="mozilla", data={"members": ["blah"]})
        # The returned groups should be strings.
        groups = self.client.get_groups(bucket="mozilla")
        self.assertEqual(2, len(groups))
        self.assertEqual(set([coll["id"] for coll in groups]), set(["receipts", "assets"]))

    def test_group_deletion(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
        self.client.delete_group(id="payments", bucket="mozilla")
        assert len(self.client.get_groups(bucket="mozilla")) == 0

    def test_group_deletion_if_exists(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
        self.client.delete_group(id="payments", bucket="mozilla")
        self.client.delete_group(id="payments", bucket="mozilla", if_exists=True)

    def test_group_deletion_can_still_raise_errors(self):
        error = KintoException("An error occured")
        with mock.patch.object(self.client.session, "request", side_effect=error):
            with pytest.raises(KintoException):
                self.client.delete_group(id="payments", bucket="mozilla", if_exists=True)

    def test_groups_deletion(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_group(id="amo", bucket="mozilla", data={"members": ["blah"]})
        self.client.create_group(id="blocklist", bucket="mozilla", data={"members": ["blah"]})
        self.client.delete_groups(bucket="mozilla")
        assert len(self.client.get_groups(bucket="mozilla")) == 0

    def test_groups_deletion_when_no_groups_exist(self):
        self.client.create_bucket(id="mozilla")
        deleted_groups = self.client.delete_groups(bucket="mozilla")
        assert len(deleted_groups) == 0

    def test_collection_creation(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(
            id="payments", bucket="mozilla", permissions={"write": ["account:alexis"]}
        )

        # Test retrieval of a collection gets the permissions as well.
        collection = self.client.get_collection(id="payments", bucket="mozilla")
        assert "account:alexis" in collection["permissions"]["write"]

    def test_collection_not_found(self):
        self.client.create_bucket(id="mozilla")

        with pytest.raises(CollectionNotFound):
            self.client.get_collection(id="payments", bucket="mozilla")

    def test_collection_access_forbidden(self):
        with pytest.raises(KintoException):
            self.client.get_collection(id="payments", bucket="mozilla")

    def test_collection_creation_if_not_exists(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(id="payments", bucket="mozilla")
        # Should not raise.
        self.client.create_collection(id="payments", bucket="mozilla", if_not_exists=True)

    def test_collection_list(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(id="receipts", bucket="mozilla")
        self.client.create_collection(id="assets", bucket="mozilla")

        # The returned collections should be strings.
        collections = self.client.get_collections(bucket="mozilla")
        self.assertEqual(len(collections), 2)

        self.assertEqual(set([coll["id"] for coll in collections]), set(["receipts", "assets"]))

    def test_collection_deletion(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(id="payments", bucket="mozilla")
        self.client.delete_collection(id="payments", bucket="mozilla")
        assert len(self.client.get_collections(bucket="mozilla")) == 0

    def test_collection_deletion_if_exists(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(id="payments", bucket="mozilla")
        self.client.delete_collection(id="payments", bucket="mozilla")
        self.client.delete_collection(id="payments", bucket="mozilla", if_exists=True)

    def test_collection_deletion_can_still_raise_errors(self):
        error = KintoException("An error occured")
        with mock.patch.object(self.client.session, "request", side_effect=error):
            with pytest.raises(KintoException):
                self.client.delete_collection(id="payments", bucket="mozilla", if_exists=True)

    def test_collections_deletion(self):
        self.client.create_bucket(id="mozilla")
        self.client.create_collection(id="amo", bucket="mozilla")
        self.client.create_collection(id="blocklist", bucket="mozilla")
        self.client.delete_collections(bucket="mozilla")
        assert len(self.client.get_collections(bucket="mozilla")) == 0

    def test_collections_deletion_when_no_collections_exist(self):
        self.client.create_bucket(id="mozilla")
        deleted_collections = self.client.delete_collections(bucket="mozilla")
        assert len(deleted_collections) == 0

    def test_record_creation_and_retrieval(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        created = client.create_record(
            data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
        )
        record = client.get_record(id=created["data"]["id"])
        assert "account:alexis" in record["permissions"]["read"]

    def test_records_list_retrieval(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
        records = client.get_records()
        assert len(records) == 1

    def test_records_timestamp_retrieval(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        record = client.create_record(
            data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
        )
        etag = client.get_records_timestamp()
        assert str(etag) == str(record["data"]["last_modified"])

    def test_records_paginated_list_retrieval(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        for i in range(10):
            client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
        # Kinto is running with kinto.paginate_by = 5
        records = client.get_records()
        assert len(records) == 10

    def test_records_generator_retrieval(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        for i in range(10):
            client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})

        pages = list(client.get_paginated_records())

        assert len(pages) == 2

    def test_single_record_save(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        created = client.create_record(
            data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
        )
        created["data"]["bar"] = "baz"

        # XXX enhance this in order to have to pass only one argument, created.
        client.update_record(id=created["data"]["id"], data=created["data"])

        retrieved = client.get_record(id=created["data"]["id"])
        assert "account:alexis" in retrieved["permissions"]["read"]
        assert retrieved["data"]["foo"] == u"bar"
        assert retrieved["data"]["bar"] == u"baz"
        assert created["data"]["id"] == retrieved["data"]["id"]

    def test_single_record_doesnt_overwrite(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        created = client.create_record(
            data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
        )

        with self.assertRaises(KintoException):
            # Create a second record with the ID of the first one.
            client.create_record(data={"id": created["data"]["id"], "bar": "baz"})

    def test_single_record_creation_if_not_exists(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        created = client.create_record(data={"foo": "bar"})
        client.create_record(data={"id": created["data"]["id"], "bar": "baz"}, if_not_exists=True)

    def test_single_record_can_overwrite(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        created = client.create_record(
            data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
        )

        client.create_record(data={"id": created["data"]["id"], "bar": "baz"}, safe=False)

    def test_one_record_deletion(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        record = client.create_record(data={"foo": "bar"})
        deleted = client.delete_record(id=record["data"]["id"])
        assert deleted["deleted"] is True
        assert len(client.get_records()) == 0

    def test_record_deletion_if_exists(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        record = client.create_record(data={"foo": "bar"})
        deleted = client.delete_record(id=record["data"]["id"])
        deleted_if_exists = client.delete_record(id=record["data"]["id"], if_exists=True)
        assert deleted["deleted"] is True
        assert deleted_if_exists is None

    def test_multiple_record_deletion(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        client.create_record(data={"foo": "bar"})
        client.delete_records()
        assert len(client.get_records()) == 0

    def test_records_deletion_when_no_records_exist(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()
        deleted_records = client.delete_records()
        assert len(deleted_records) == 0

    def test_bucket_sharing(self):
        alice_credentials = ("alice", "p4ssw0rd")
        alice_userid = self.get_user_id(alice_credentials)

        # Create a bucket and share it with alice.
        self.client.create_bucket(id="shared-bucket", permissions={"read": [alice_userid]})

        alice_client = Client(server_url=self.server_url, auth=alice_credentials)
        alice_client.get_bucket(id="shared-bucket")

    def test_updating_data_on_a_group(self):
        client = Client(server_url=self.server_url, auth=self.auth, bucket="mozilla")
        client.create_bucket()
        client.create_group(id="payments", data={"members": []})
        client.patch_group(id="payments", data={"secret": "psssssst!"})
        group = client.get_group(id="payments")
        assert group["data"]["secret"] == "psssssst!"

    def test_updating_data_on_a_collection(self):
        client = Client(
            server_url=self.server_url, auth=self.auth, bucket="mozilla", collection="payments"
        )
        client.create_bucket()
        client.create_collection()

        client.patch_collection(data={"secret": "psssssst!"})
        collection = client.get_collection()
        assert collection["data"]["secret"] == "psssssst!"

    def test_collection_sharing(self):
        alice_credentials = ("alice", "p4ssw0rd")
        alice_userid = self.get_user_id(alice_credentials)

        self.client.create_bucket(id="bob-bucket")
        self.client.create_collection(
            id="shared", bucket="bob-bucket", permissions={"read": [alice_userid]}
        )

        # Try to read the collection as Alice.
        alice_client = Client(server_url=self.server_url, auth=alice_credentials)
        alice_client.get_collection(id="shared", bucket="bob-bucket")

    def test_record_sharing(self):
        alice_credentials = ("alice", "p4ssw0rd")
        alice_userid = self.get_user_id(alice_credentials)

        # Create a record, and share it with Alice.
        self.client.create_bucket(id="bob-bucket")
        self.client.create_collection(id="bob-personal-collection", bucket="bob-bucket")
        record = self.client.create_record(
            data={"foo": "bar"},
            permissions={"read": [alice_userid]},
            bucket="bob-bucket",
            collection="bob-personal-collection",
        )

        # Try to read the record as Alice
        alice_client = Client(server_url=self.server_url, auth=alice_credentials)
        record = alice_client.get_record(
            id=record["data"]["id"], bucket="bob-bucket", collection="bob-personal-collection"
        )

        assert record["data"]["foo"] == "bar"

    def test_request_batching(self):
        with self.client.batch(bucket="mozilla", collection="fonts") as batch:
            batch.create_bucket()
            batch.create_collection()
            batch.create_record(data={"foo": "bar"}, permissions={"read": ["natim"]})
            batch.create_record(data={"bar": "baz"}, permissions={"read": ["account:alexis"]})

        _, _, r1, r2 = batch.results()
        records = self.client.get_records(bucket="mozilla", collection="fonts")

        assert len(records) == 2
        assert records[0] == r2["data"]
        assert records[1] == r1["data"]

    def test_patch_record_jsonpatch(self):
        self.client.create_bucket(id="b1")
        self.client.create_collection(id="c1", bucket="b1")
        self.client.create_record(id="r1", collection="c1", bucket="b1", data={"hello": "world"})
        patch = JSONPatch(
            [
                {"op": "add", "path": "/data/goodnight", "value": "moon"},
                {"op": "add", "path": "/permissions/read/alice"},
            ]
        )
        self.client.patch_record(id="r1", collection="c1", bucket="b1", changes=patch)
        record = self.client.get_record(bucket="b1", collection="c1", id="r1")
        assert record["data"]["hello"] == "world"
        assert record["data"]["goodnight"] == "moon"
        assert record["permissions"]["read"] == ["alice"]

    def test_replication(self):
        # First, create a few records on the first kinto collection.
        with self.client.batch(bucket="origin", collection="coll") as batch:
            batch.create_bucket()
            batch.create_collection()

            for n in range(10):
                batch.create_record(data={"foo": "bar", "n": n})

        origin = Client(
            server_url=self.server_url, auth=self.auth, bucket="origin", collection="coll"
        )
        destination = Client(
            server_url=self.server_url, auth=self.auth, bucket="destination", collection="coll"
        )

        replication.replicate(origin, destination)
        records = self.client.get_records(bucket="destination", collection="coll")
        assert len(records) == 10


if __name__ == "__main__":
    unittest.main()

import os.path
from unittest import mock

import pytest

from kinto_http import BucketNotFound, CollectionNotFound, KintoException, replication
from kinto_http.patch_type import JSONPatch

from .support import get_user_id


__HERE__ = os.path.abspath(os.path.dirname(__file__))


def test_bucket_creation(functional_setup):
    client = functional_setup
    bucket = client.create_bucket(id="mozilla")
    user_id = get_user_id(client.session.server_url, client.session.auth)
    assert user_id in bucket["permissions"]["write"]


def test_bucket_creation_if_not_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    # Should not raise.
    client.create_bucket(id="mozilla", if_not_exists=True)


def test_buckets_retrieval(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    buckets = client.get_buckets()
    assert len(buckets) == 1


def test_bucket_retrieval(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.get_bucket(id="mozilla")
    # XXX Add permissions handling during creation and check they are
    # present during retrieval.


def test_bucket_modification(functional_setup):
    client = functional_setup
    bucket = client.create_bucket(id="mozilla", data={"version": 1})
    assert bucket["data"]["version"] == 1
    bucket = client.patch_bucket(id="mozilla", data={"author": "you"})
    assert bucket["data"]["version"] == 1
    assert bucket["data"]["author"] == "you"
    bucket = client.update_bucket(id="mozilla", data={"date": "today"})
    assert bucket["data"]["date"] == "today"
    assert "version" not in bucket["data"]


def test_bucket_retrieval_fails_when_not_created(functional_setup):
    client = functional_setup
    with pytest.raises(BucketNotFound):
        client.get_bucket(id="non-existent")


def test_bucket_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.delete_bucket(id="mozilla")
    with pytest.raises(BucketNotFound):
        client.get_bucket(id="mozilla")


def test_bucket_deletion_if_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.delete_bucket(id="mozilla")
    client.delete_bucket(id="mozilla", if_exists=True)


def test_buckets_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    buckets = client.delete_buckets()
    assert buckets[0]["id"] == "mozilla"
    with pytest.raises(BucketNotFound):
        client.get_bucket(id="mozilla")


def test_buckets_deletion_when_no_buckets_exist(functional_setup):
    client = functional_setup
    deleted_buckets = client.delete_buckets()
    assert len(deleted_buckets) == 0


def test_bucket_save(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla", permissions={"write": ["account:alexis"]})
    bucket = client.get_bucket(id="mozilla")
    assert "account:alexis" in bucket["permissions"]["write"]


def test_group_creation(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(
        id="payments",
        bucket="mozilla",
        data={"members": ["blah"]},
        permissions={"write": ["blah"]},
    )
    # Test retrieval of a group gets the permissions as well.
    group = client.get_group(id="payments", bucket="mozilla")
    assert "blah" in group["permissions"]["write"]


def test_group_creation_if_not_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    client.create_group(
        id="payments",
        bucket="mozilla",
        data={"members": ["blah"]},
        permissions={"write": ["blah"]},
        if_not_exists=True,
    )


def test_group_creation_if_bucket_does_not_exist(functional_setup):
    client = functional_setup
    with pytest.raises(KintoException) as e:
        client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    assert str(e.value).endswith(
        "PUT /v1/buckets/mozilla/groups/payments - "
        "403 Unauthorized. Please check that the "
        "bucket exists and that you have the permission "
        "to create or write on this group."
    )


def test_group_update(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    group = client.create_group(
        id="payments", bucket="mozilla", data={"members": ["blah"]}, if_not_exists=True
    )
    assert group["data"]["members"][0] == "blah"
    group = client.update_group(data={"members": ["blah", "foo"]}, id="payments", bucket="mozilla")
    assert group["data"]["members"][1] == "foo"


def test_group_list(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(id="receipts", bucket="mozilla", data={"members": ["blah"]})
    client.create_group(id="assets", bucket="mozilla", data={"members": ["blah"]})
    # The returned groups should be strings.
    groups = client.get_groups(bucket="mozilla")
    assert 2 == len(groups)
    assert set([coll["id"] for coll in groups]) == set(["receipts", "assets"])


def test_group_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    client.delete_group(id="payments", bucket="mozilla")
    assert len(client.get_groups(bucket="mozilla")) == 0


def test_group_deletion_if_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    client.delete_group(id="payments", bucket="mozilla")
    client.delete_group(id="payments", bucket="mozilla", if_exists=True)


def test_group_deletion_can_still_raise_errors(functional_setup):
    client = functional_setup
    error = KintoException("An error occured")
    with mock.patch.object(client.session, "request", side_effect=error):
        with pytest.raises(KintoException):
            client.delete_group(id="payments", bucket="mozilla", if_exists=True)


def test_groups_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_group(id="amo", bucket="mozilla", data={"members": ["blah"]})
    client.create_group(id="blocklist", bucket="mozilla", data={"members": ["blah"]})
    client.delete_groups(bucket="mozilla")
    assert len(client.get_groups(bucket="mozilla")) == 0


def test_groups_deletion_when_no_groups_exist(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    deleted_groups = client.delete_groups(bucket="mozilla")
    assert len(deleted_groups) == 0


def test_collection_creation(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(
        id="payments", bucket="mozilla", permissions={"write": ["account:alexis"]}
    )

    # Test retrieval of a collection gets the permissions as well.
    collection = client.get_collection(id="payments", bucket="mozilla")
    assert "account:alexis" in collection["permissions"]["write"]


def test_collection_not_found(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")

    with pytest.raises(CollectionNotFound):
        client.get_collection(id="payments", bucket="mozilla")


def test_collection_access_forbidden(functional_setup):
    client = functional_setup
    with pytest.raises(KintoException):
        client.get_collection(id="payments", bucket="mozilla")


def test_collection_creation_if_not_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(id="payments", bucket="mozilla")
    # Should not raise.
    client.create_collection(id="payments", bucket="mozilla", if_not_exists=True)


def test_collection_list(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(id="receipts", bucket="mozilla")
    client.create_collection(id="assets", bucket="mozilla")

    # The returned collections should be strings.
    collections = client.get_collections(bucket="mozilla")
    assert len(collections) == 2

    assert set([coll["id"] for coll in collections]) == set(["receipts", "assets"])


def test_collection_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(id="payments", bucket="mozilla")
    client.delete_collection(id="payments", bucket="mozilla")
    assert len(client.get_collections(bucket="mozilla")) == 0


def test_collection_deletion_if_exists(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(id="payments", bucket="mozilla")
    client.delete_collection(id="payments", bucket="mozilla")
    client.delete_collection(id="payments", bucket="mozilla", if_exists=True)


def test_collection_deletion_can_still_raise_errors(functional_setup):
    client = functional_setup
    error = KintoException("An error occured")
    with mock.patch.object(client.session, "request", side_effect=error):
        with pytest.raises(KintoException):
            client.delete_collection(id="payments", bucket="mozilla", if_exists=True)


def test_collections_deletion(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    client.create_collection(id="amo", bucket="mozilla")
    client.create_collection(id="blocklist", bucket="mozilla")
    client.delete_collections(bucket="mozilla")
    assert len(client.get_collections(bucket="mozilla")) == 0


def test_collections_deletion_when_no_collections_exist(functional_setup):
    client = functional_setup
    client.create_bucket(id="mozilla")
    deleted_collections = client.delete_collections(bucket="mozilla")
    assert len(deleted_collections) == 0


def test_record_creation_and_retrieval(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    created = client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    record = client.get_record(id=created["data"]["id"])
    assert "account:alexis" in record["permissions"]["read"]


def test_records_list_retrieval(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    records = client.get_records()
    assert len(records) == 1


def test_records_timestamp_retrieval(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    record = client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    etag = client.get_records_timestamp()
    assert str(etag) == str(record["data"]["last_modified"])


def test_records_paginated_list_retrieval(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    for _ in range(10):
        client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    # Kinto is running with kinto.paginate_by = 5
    records = client.get_records()
    assert len(records) == 10


def test_records_generator_retrieval(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    for _ in range(10):
        client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})

    pages = list(client.get_paginated_records())

    assert len(pages) == 2


def test_single_record_save(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    created = client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    created["data"]["bar"] = "baz"

    # XXX enhance this in order to have to pass only one argument, created.
    client.update_record(id=created["data"]["id"], data=created["data"])

    retrieved = client.get_record(id=created["data"]["id"])
    assert "account:alexis" in retrieved["permissions"]["read"]
    assert retrieved["data"]["foo"] == "bar"
    assert retrieved["data"]["bar"] == "baz"
    assert created["data"]["id"] == retrieved["data"]["id"]


def test_single_record_doesnt_overwrite(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    created = client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})

    with pytest.raises(KintoException):
        # Create a second record with the ID of the first one.
        client.create_record(data={"id": created["data"]["id"], "bar": "baz"})


def test_single_record_creation_if_not_exists(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    created = client.create_record(data={"foo": "bar"})
    client.create_record(data={"id": created["data"]["id"], "bar": "baz"}, if_not_exists=True)


def test_single_record_can_overwrite(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    created = client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})

    client.create_record(data={"id": created["data"]["id"], "bar": "baz"}, safe=False)


def test_one_record_deletion(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    record = client.create_record(data={"foo": "bar"})
    deleted = client.delete_record(id=record["data"]["id"])
    assert deleted["deleted"] is True
    assert len(client.get_records()) == 0


def test_record_deletion_if_exists(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    record = client.create_record(data={"foo": "bar"})
    deleted = client.delete_record(id=record["data"]["id"])
    deleted_if_exists = client.delete_record(id=record["data"]["id"], if_exists=True)
    assert deleted["deleted"] is True
    assert deleted_if_exists is None


def test_multiple_record_deletion(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    client.create_record(data={"foo": "bar"})
    client.delete_records()
    assert len(client.get_records()) == 0


def test_records_deletion_when_no_records_exist(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()
    deleted_records = client.delete_records()
    assert len(deleted_records) == 0


def test_bucket_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(client.session.server_url, alice_credentials)

    # Create a bucket and share it with alice.
    client.create_bucket(id="shared-bucket", permissions={"read": [alice_userid]})

    alice_client = client.clone(auth=alice_credentials)
    alice_client.get_bucket(id="shared-bucket")


def test_updating_data_on_a_group(functional_setup):
    client = functional_setup.clone(bucket="mozilla")
    client.create_bucket()
    client.create_group(id="payments", data={"members": []})
    client.patch_group(id="payments", data={"secret": "psssssst!"})
    group = client.get_group(id="payments")
    assert group["data"]["secret"] == "psssssst!"


def test_updating_data_on_a_collection(functional_setup):
    client = functional_setup.clone(bucket="mozilla", collection="payments")
    client.create_bucket()
    client.create_collection()

    client.patch_collection(data={"secret": "psssssst!"})
    collection = client.get_collection()
    assert collection["data"]["secret"] == "psssssst!"


def test_collection_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(client.session.server_url, alice_credentials)

    client.create_bucket(id="bob-bucket")
    client.create_collection(
        id="shared", bucket="bob-bucket", permissions={"read": [alice_userid]}
    )

    # Try to read the collection as Alice.
    alice_client = client.clone(auth=alice_credentials)
    alice_client.get_collection(id="shared", bucket="bob-bucket")


def test_record_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(client.session.server_url, alice_credentials)

    # Create a record, and share it with Alice.
    client.create_bucket(id="bob-bucket")
    client.create_collection(id="bob-personal-collection", bucket="bob-bucket")
    record = client.create_record(
        data={"foo": "bar"},
        permissions={"read": [alice_userid]},
        bucket="bob-bucket",
        collection="bob-personal-collection",
    )

    # Try to read the record as Alice
    alice_client = client.clone(auth=alice_credentials)
    record = alice_client.get_record(
        id=record["data"]["id"], bucket="bob-bucket", collection="bob-personal-collection"
    )

    assert record["data"]["foo"] == "bar"


def test_request_batching(functional_setup):
    client = functional_setup
    with client.batch(bucket="mozilla", collection="fonts") as batch:
        batch.create_bucket()
        batch.create_collection()
        batch.create_record(data={"foo": "bar"}, permissions={"read": ["natim"]})
        batch.create_record(data={"bar": "baz"}, permissions={"read": ["account:alexis"]})

    _, _, r1, r2 = batch.results()
    records = client.get_records(bucket="mozilla", collection="fonts")

    assert len(records) == 2
    assert records[0] == r2["data"]
    assert records[1] == r1["data"]


def test_patch_record_jsonpatch(functional_setup):
    client = functional_setup
    client.create_bucket(id="b1")
    client.create_collection(id="c1", bucket="b1")
    client.create_record(id="r1", collection="c1", bucket="b1", data={"hello": "world"})
    patch = JSONPatch(
        [
            {"op": "add", "path": "/data/goodnight", "value": "moon"},
            {"op": "add", "path": "/permissions/read/alice"},
        ]
    )
    client.patch_record(id="r1", collection="c1", bucket="b1", changes=patch)
    record = client.get_record(bucket="b1", collection="c1", id="r1")
    assert record["data"]["hello"] == "world"
    assert record["data"]["goodnight"] == "moon"
    assert record["permissions"]["read"] == ["alice"]


def test_replication(functional_setup):
    client = functional_setup
    # First, create a few records on the first kinto collection.
    with client.batch(bucket="origin", collection="coll") as batch:
        batch.create_bucket()
        batch.create_collection()

        for n in range(10):
            batch.create_record(data={"foo": "bar", "n": n})

    origin = client.clone(bucket="origin", collection="coll")
    destination = client.clone(bucket="destination", collection="coll")

    replication.replicate(origin, destination)
    records = client.get_records(bucket="destination", collection="coll")
    assert len(records) == 10

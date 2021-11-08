import hashlib
import hmac
from typing import Dict, Tuple
from urllib.parse import urljoin

import pytest
import requests
from pytest_mock import MockerFixture

from kinto_http import AsyncClient as Client
from kinto_http import BucketNotFound, CollectionNotFound, KintoException
from kinto_http.patch_type import JSONPatch


SERVER_URL = "http://localhost:8888/v1"
DEFAULT_AUTH = ("user", "p4ssw0rd")


# Backported from kinto.core.utils
def hmac_digest(secret, message, encoding="utf-8") -> hmac.HMAC:
    """Return hex digest of a message HMAC using secret"""
    if isinstance(secret, str):
        secret = secret.encode(encoding)
    return hmac.new(secret, message.encode(encoding), hashlib.sha256).hexdigest()


def create_user(server_url: str, credentials: Tuple[str, str]) -> Dict:
    account_url = urljoin(server_url, "/accounts/{}".format(credentials[0]))
    r = requests.put(account_url, json={"data": {"password": credentials[1]}}, auth=DEFAULT_AUTH)
    r.raise_for_status()
    return r.json()


def get_user_id(server_url: str, credentials: Tuple[str, str]) -> str:
    r = create_user(server_url, credentials)
    return f"account:{r['data']['id']}"


@pytest.mark.asyncio
async def test_bucket_creation(functional_setup):
    client = functional_setup
    bucket = await client.create_bucket(id="mozilla")
    user_id = get_user_id(SERVER_URL, DEFAULT_AUTH)
    assert user_id in bucket["permissions"]["write"]


@pytest.mark.asyncio
async def test_bucket_creation_if_not_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    # Should not raise.
    await client.create_bucket(id="mozilla", if_not_exists=True)


@pytest.mark.asyncio
async def test_buckets_retrieval(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    buckets = await client.get_buckets()
    assert len(buckets) == 1


@pytest.mark.asyncio
async def test_bucket_retrieval(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.get_bucket(id="mozilla")
    # XXX Add permissions handling during creation and check they are
    # present during retrieval.


@pytest.mark.asyncio
async def test_bucket_modification(functional_setup):
    client = functional_setup
    bucket = await client.create_bucket(id="mozilla", data={"version": 1})
    assert bucket["data"]["version"] == 1
    bucket = await client.patch_bucket(id="mozilla", data={"author": "you"})
    assert bucket["data"]["version"] == 1
    assert bucket["data"]["author"] == "you"
    bucket = await client.update_bucket(id="mozilla", data={"date": "today"})
    assert bucket["data"]["date"] == "today"
    assert "version" not in bucket["data"]


@pytest.mark.asyncio
async def test_bucket_retrieval_fails_when_not_created(functional_setup):
    client = functional_setup
    with pytest.raises(BucketNotFound):
        await client.get_bucket(id="non-existent")


@pytest.mark.asyncio
async def test_bucket_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.delete_bucket(id="mozilla")
    with pytest.raises(BucketNotFound):
        await client.get_bucket(id="mozilla")


@pytest.mark.asyncio
async def test_bucket_deletion_if_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.delete_bucket(id="mozilla")
    await client.delete_bucket(id="mozilla", if_exists=True)


@pytest.mark.asyncio
async def test_buckets_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    buckets = await client.delete_buckets()
    assert buckets[0]["id"] == "mozilla"
    with pytest.raises(BucketNotFound):
        await client.get_bucket(id="mozilla")


@pytest.mark.asyncio
async def test_buckets_deletion_when_no_buckets_exist(functional_setup):
    client = functional_setup
    deleted_buckets = await client.delete_buckets()
    assert len(deleted_buckets) == 0


@pytest.mark.asyncio
async def test_bucket_save(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla", permissions={"write": ["account:alexis"]})
    bucket = await client.get_bucket(id="mozilla")
    assert "account:alexis" in bucket["permissions"]["write"]


@pytest.mark.asyncio
async def test_group_creation(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(
        id="payments",
        bucket="mozilla",
        data={"members": ["blah"]},
        permissions={"write": ["blah"]},
    )
    # Test retrieval of a group gets the permissions as well.
    group = await client.get_group(id="payments", bucket="mozilla")
    assert "blah" in group["permissions"]["write"]


@pytest.mark.asyncio
async def test_group_creation_if_not_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    await client.create_group(
        id="payments",
        bucket="mozilla",
        data={"members": ["blah"]},
        permissions={"write": ["blah"]},
        if_not_exists=True,
    )


@pytest.mark.asyncio
async def test_group_creation_if_bucket_does_not_exist(functional_setup):
    client = functional_setup
    with pytest.raises(KintoException) as e:
        await client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    assert str(e.value).endswith(
        "PUT /v1/buckets/mozilla/groups/payments - "
        "403 Unauthorized. Please check that the "
        "bucket exists and that you have the permission "
        "to create or write on this group."
    )


@pytest.mark.asyncio
async def test_group_update(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    group = await client.create_group(
        id="payments", bucket="mozilla", data={"members": ["blah"]}, if_not_exists=True
    )
    assert group["data"]["members"][0] == "blah"
    group = await client.update_group(
        data={"members": ["blah", "foo"]}, id="payments", bucket="mozilla"
    )
    assert group["data"]["members"][1] == "foo"


@pytest.mark.asyncio
async def test_group_list(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(id="receipts", bucket="mozilla", data={"members": ["blah"]})
    await client.create_group(id="assets", bucket="mozilla", data={"members": ["blah"]})
    # The returned groups should be strings.
    groups = await client.get_groups(bucket="mozilla")
    assert 2 == len(groups)
    assert set([coll["id"] for coll in groups]) == set(["receipts", "assets"])


@pytest.mark.asyncio
async def test_group_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    await client.delete_group(id="payments", bucket="mozilla")
    assert len(await client.get_groups(bucket="mozilla")) == 0


@pytest.mark.asyncio
async def test_group_deletion_if_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(id="payments", bucket="mozilla", data={"members": ["blah"]})
    await client.delete_group(id="payments", bucket="mozilla")
    await client.delete_group(id="payments", bucket="mozilla", if_exists=True)


@pytest.mark.asyncio
async def test_group_deletion_can_still_raise_errors(functional_setup, mocker: MockerFixture):
    client = functional_setup
    error = KintoException("An error occured")
    mocker.patch.object(client.session, "request", side_effect=error)
    with pytest.raises(KintoException):
        await client.delete_group(id="payments", bucket="mozilla", if_exists=True)


@pytest.mark.asyncio
async def test_groups_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_group(id="amo", bucket="mozilla", data={"members": ["blah"]})
    await client.create_group(id="blocklist", bucket="mozilla", data={"members": ["blah"]})
    await client.delete_groups(bucket="mozilla")
    assert len(await client.get_groups(bucket="mozilla")) == 0


@pytest.mark.asyncio
async def test_groups_deletion_when_no_groups_exist(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    deleted_groups = await client.delete_groups(bucket="mozilla")
    assert len(deleted_groups) == 0


@pytest.mark.asyncio
async def test_collection_creation(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(
        id="payments", bucket="mozilla", permissions={"write": ["account:alexis"]}
    )

    # Test retrieval of a collection gets the permissions as well.
    collection = await client.get_collection(id="payments", bucket="mozilla")
    assert "account:alexis" in collection["permissions"]["write"]


@pytest.mark.asyncio
async def test_collection_not_found(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")

    with pytest.raises(CollectionNotFound):
        await client.get_collection(id="payments", bucket="mozilla")


@pytest.mark.asyncio
async def test_collection_access_forbidden(functional_setup):
    client = functional_setup
    with pytest.raises(KintoException):
        await client.get_collection(id="payments", bucket="mozilla")


@pytest.mark.asyncio
async def test_collection_creation_if_not_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(id="payments", bucket="mozilla")
    # Should not raise.
    await client.create_collection(id="payments", bucket="mozilla", if_not_exists=True)


@pytest.mark.asyncio
async def test_collection_list(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(id="receipts", bucket="mozilla")
    await client.create_collection(id="assets", bucket="mozilla")

    # The returned collections should be strings.
    collections = await client.get_collections(bucket="mozilla")
    assert len(collections) == 2

    assert set([coll["id"] for coll in collections]) == set(["receipts", "assets"])


@pytest.mark.asyncio
async def test_collection_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(id="payments", bucket="mozilla")
    await client.delete_collection(id="payments", bucket="mozilla")
    assert len(await client.get_collections(bucket="mozilla")) == 0


@pytest.mark.asyncio
async def test_collection_deletion_if_exists(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(id="payments", bucket="mozilla")
    await client.delete_collection(id="payments", bucket="mozilla")
    await client.delete_collection(id="payments", bucket="mozilla", if_exists=True)


@pytest.mark.asyncio
async def test_collection_deletion_can_still_raise_errors(functional_setup, mocker: MockerFixture):
    client = functional_setup
    error = KintoException("An error occured")
    mocker.patch.object(client.session, "request", side_effect=error)
    with pytest.raises(KintoException):
        await client.delete_collection(id="payments", bucket="mozilla", if_exists=True)


@pytest.mark.asyncio
async def test_collections_deletion(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    await client.create_collection(id="amo", bucket="mozilla")
    await client.create_collection(id="blocklist", bucket="mozilla")
    await client.delete_collections(bucket="mozilla")
    assert len(await client.get_collections(bucket="mozilla")) == 0


@pytest.mark.asyncio
async def test_collections_deletion_when_no_collections_exist(functional_setup):
    client = functional_setup
    await client.create_bucket(id="mozilla")
    deleted_collections = await client.delete_collections(bucket="mozilla")
    assert len(deleted_collections) == 0


@pytest.mark.asyncio
async def test_record_creation_and_retrieval(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    created = await client.create_record(
        data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
    )
    record = await client.get_record(id=created["data"]["id"])
    assert "account:alexis" in record["permissions"]["read"]


@pytest.mark.asyncio
async def test_records_list_retrieval(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    await client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    records = await client.get_records()
    assert len(records) == 1


@pytest.mark.asyncio
async def test_records_timestamp_retrieval(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    record = await client.create_record(
        data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
    )
    etag = await client.get_records_timestamp()
    assert str(etag) == str(record["data"]["last_modified"])


@pytest.mark.asyncio
async def test_records_paginated_list_retrieval(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    for _ in range(10):
        await client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})
    # Kinto is running with kinto.paginate_by = 5
    records = await client.get_records()
    assert len(records) == 10


@pytest.mark.asyncio
async def test_records_generator_retrieval(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    for _ in range(10):
        await client.create_record(data={"foo": "bar"}, permissions={"read": ["account:alexis"]})

    pages = list(await client.get_paginated_records())

    assert len(pages) == 2


@pytest.mark.asyncio
async def test_single_record_save(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    created = await client.create_record(
        data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
    )
    created["data"]["bar"] = "baz"

    # XXX enhance this in order to have to pass only one argument, created.
    await client.update_record(id=created["data"]["id"], data=created["data"])

    retrieved = await client.get_record(id=created["data"]["id"])
    assert "account:alexis" in retrieved["permissions"]["read"]
    assert retrieved["data"]["foo"] == "bar"
    assert retrieved["data"]["bar"] == "baz"
    assert created["data"]["id"] == retrieved["data"]["id"]


@pytest.mark.asyncio
async def test_single_record_doesnt_overwrite(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    created = await client.create_record(
        data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
    )

    with pytest.raises(KintoException):
        # Create a second record with the ID of the first one.
        await client.create_record(data={"id": created["data"]["id"], "bar": "baz"})


@pytest.mark.asyncio
async def test_single_record_creation_if_not_exists(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    created = await client.create_record(data={"foo": "bar"})
    await client.create_record(
        data={"id": created["data"]["id"], "bar": "baz"}, if_not_exists=True
    )


@pytest.mark.asyncio
async def test_single_record_can_overwrite(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    created = await client.create_record(
        data={"foo": "bar"}, permissions={"read": ["account:alexis"]}
    )

    await client.create_record(data={"id": created["data"]["id"], "bar": "baz"}, safe=False)


@pytest.mark.asyncio
async def test_one_record_deletion(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    record = await client.create_record(data={"foo": "bar"})
    deleted = await client.delete_record(id=record["data"]["id"])
    assert deleted["deleted"] is True
    assert len(await client.get_records()) == 0


@pytest.mark.asyncio
async def test_record_deletion_if_exists(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    record = await client.create_record(data={"foo": "bar"})
    deleted = await client.delete_record(id=record["data"]["id"])
    deleted_if_exists = await client.delete_record(id=record["data"]["id"], if_exists=True)
    assert deleted["deleted"] is True
    assert deleted_if_exists is None


@pytest.mark.asyncio
async def test_multiple_record_deletion(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    await client.create_record(data={"foo": "bar"})
    await client.delete_records()
    assert len(await client.get_records()) == 0


@pytest.mark.asyncio
async def test_records_deletion_when_no_records_exist(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()
    deleted_records = await client.delete_records()
    assert len(deleted_records) == 0


@pytest.mark.asyncio
async def test_bucket_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(SERVER_URL, alice_credentials)

    # Create a bucket and share it with alice.
    await client.create_bucket(id="shared-bucket", permissions={"read": [alice_userid]})

    alice_client = Client(server_url=SERVER_URL, auth=alice_credentials)
    await alice_client.get_bucket(id="shared-bucket")


@pytest.mark.asyncio
async def test_updating_data_on_a_group(functional_setup):
    client = Client(server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla")
    await client.create_bucket()
    await client.create_group(id="payments", data={"members": []})
    await client.patch_group(id="payments", data={"secret": "psssssst!"})
    group = await client.get_group(id="payments")
    assert group["data"]["secret"] == "psssssst!"


@pytest.mark.asyncio
async def test_updating_data_on_a_collection(functional_setup):
    client = Client(
        server_url=SERVER_URL, auth=DEFAULT_AUTH, bucket="mozilla", collection="payments"
    )
    await client.create_bucket()
    await client.create_collection()

    await client.patch_collection(data={"secret": "psssssst!"})
    collection = await client.get_collection()
    assert collection["data"]["secret"] == "psssssst!"


@pytest.mark.asyncio
async def test_collection_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(SERVER_URL, alice_credentials)

    await client.create_bucket(id="bob-bucket")
    await client.create_collection(
        id="shared", bucket="bob-bucket", permissions={"read": [alice_userid]}
    )

    # Try to read the collection as Alice.
    alice_client = Client(server_url=SERVER_URL, auth=alice_credentials)
    await alice_client.get_collection(id="shared", bucket="bob-bucket")


@pytest.mark.asyncio
async def test_record_sharing(functional_setup):
    client = functional_setup
    alice_credentials = ("alice", "p4ssw0rd")
    alice_userid = get_user_id(SERVER_URL, alice_credentials)

    # Create a record, and share it with Alice.
    await client.create_bucket(id="bob-bucket")
    await client.create_collection(id="bob-personal-collection", bucket="bob-bucket")
    record = await client.create_record(
        data={"foo": "bar"},
        permissions={"read": [alice_userid]},
        bucket="bob-bucket",
        collection="bob-personal-collection",
    )

    # Try to read the record as Alice
    alice_client = Client(server_url=SERVER_URL, auth=alice_credentials)
    record = await alice_client.get_record(
        id=record["data"]["id"], bucket="bob-bucket", collection="bob-personal-collection"
    )

    assert record["data"]["foo"] == "bar"


@pytest.mark.asyncio
async def test_patch_record_jsonpatch(functional_setup):
    client = functional_setup
    await client.create_bucket(id="b1")
    await client.create_collection(id="c1", bucket="b1")
    await client.create_record(id="r1", collection="c1", bucket="b1", data={"hello": "world"})
    patch = JSONPatch(
        [
            {"op": "add", "path": "/data/goodnight", "value": "moon"},
            {"op": "add", "path": "/permissions/read/alice"},
        ]
    )
    await client.patch_record(id="r1", collection="c1", bucket="b1", changes=patch)
    record = await client.get_record(bucket="b1", collection="c1", id="r1")
    assert record["data"]["hello"] == "world"
    assert record["data"]["goodnight"] == "moon"
    assert record["permissions"]["read"] == ["alice"]

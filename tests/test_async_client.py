import re

import pytest
from pytest_mock import MockerFixture

from kinto_http import AsyncClient as Client
from kinto_http import BearerTokenAuth, BucketNotFound, KintoException
from kinto_http.constants import DO_NOT_OVERWRITE, SERVER_URL
from kinto_http.patch_type import JSONPatch, MergePatch
from kinto_http.session import create_session

from .support import build_response, get_http_error, mock_response


pytestmark = pytest.mark.asyncio


async def test_server_info(async_client_setup: Client):
    client = async_client_setup
    await client.server_info()
    client.session.request.assert_called_with("get", "/")


async def test_get_endpoint(async_client_setup: Client):
    client = async_client_setup
    actual_endpoint = await client.get_endpoint(
        "records", bucket="homebrewing", collection="recipes"
    )
    assert actual_endpoint == "/buckets/homebrewing/collections/recipes/records"


def test_auth_from_access_token(mocker: MockerFixture):
    r = mocker.MagicMock()
    r.headers = {}

    client = Client(auth=BearerTokenAuth("abc", type="Bearer+OIDC"))
    client.session.auth(r)

    assert r.headers["Authorization"] == "Bearer+OIDC abc"


def test_client_is_represented_properly_with_bucket_and_collection(async_client_setup: Client):
    client = async_client_setup.clone(
        server_url=SERVER_URL, bucket="homebrewing", collection="recipes"
    )
    expected_repr = f"<KintoAsyncClient {SERVER_URL}/buckets/homebrewing/collections/recipes>"
    assert str(client) == expected_repr


def test_client_is_represented_properly_with_bucket(async_client_setup: Client):
    client = async_client_setup.clone(server_url=SERVER_URL, bucket="homebrewing")
    expected_repr = f"<KintoAsyncClient {SERVER_URL}/buckets/homebrewing>"
    assert str(client) == expected_repr


def test_client_is_represented_properly_without_bucket(async_client_setup: Client):
    client = async_client_setup.clone(server_url=SERVER_URL, bucket=None)
    expected_repr = f"<KintoAsyncClient {SERVER_URL}/>"
    assert str(client) == expected_repr


async def test_client_uses_default_bucket_if_not_specified(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session)
    client = Client(session=client.session)
    await client.get_bucket()
    client.session.request.assert_called_with("get", "/buckets/default", params={})


def test_client_uses_passed_bucket_if_specified():
    client = Client(server_url=SERVER_URL, bucket="buck")
    assert client.bucket_name == "buck"


async def test_client_can_receive_default_headers(mocker: MockerFixture):
    r = mocker.MagicMock()
    r.status_code = 200
    client = Client(server_url="https://kinto.io/v1", headers={"Allow-Access": "CDN"})
    mocked = mocker.patch("kinto_http.session.requests")
    mocked.request.return_value = r
    await client.server_info()
    assert "Allow-Access" in mocked.request.call_args_list[0][1]["headers"]


def test_client_clone_with_auth(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(auth=("reviewer", ""))
    assert client_clone.session.auth == ("reviewer", "")
    assert client.session != client_clone.session
    assert client.session.server_url == client_clone.session.server_url
    assert client.session.auth != client_clone.session.auth
    assert client.session.nb_retry == client_clone.session.nb_retry
    assert client.session.retry_after == client_clone.session.retry_after
    assert client.bucket_name == client_clone.bucket_name
    assert client.collection_name == client_clone.collection_name


def test_client_clone_with_server_url(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(server_url=SERVER_URL)
    assert client_clone.session.server_url == SERVER_URL
    assert client.session != client_clone.session
    assert client.session.server_url != client_clone.session.server_url
    assert client.session.auth == client_clone.session.auth
    assert client.session.nb_retry == client_clone.session.nb_retry
    assert client.session.retry_after == client_clone.session.retry_after
    assert client.bucket_name == client_clone.bucket_name
    assert client.collection_name == client_clone.collection_name


def test_client_clone_with_new_session(async_client_setup: Client):
    client = async_client_setup
    session = create_session(auth=("reviewer", ""), server_url=SERVER_URL)
    client_clone = client.clone(session=session)
    assert client_clone.session == session
    assert client.session != client_clone.session
    assert client.session.server_url != client_clone.session.server_url
    assert client.session.auth != client_clone.session.auth
    assert client.bucket_name == client_clone.bucket_name
    assert client.collection_name == client_clone.collection_name


def test_client_clone_with_auth_and_server_url(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(auth=("reviewer", ""), server_url=SERVER_URL)
    assert client_clone.session.auth == ("reviewer", "")
    assert client_clone.session.server_url == SERVER_URL
    assert client.session != client_clone.session
    assert client.session.server_url != client_clone.session.server_url
    assert client.session.auth != client_clone.session.auth
    assert client.session.nb_retry == client_clone.session.nb_retry
    assert client.session.retry_after == client_clone.session.retry_after
    assert client.bucket_name == client_clone.bucket_name
    assert client.collection_name == client_clone.collection_name


def test_client_clone_with_existing_session(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(session=client.session)
    assert client.session == client_clone.session
    assert client.session.server_url == client_clone.session.server_url
    assert client.session.auth == client_clone.session.auth
    assert client.bucket_name == client_clone.bucket_name
    assert client.collection_name == client_clone.collection_name


def test_client_clone_with_new_bucket_and_collection(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(bucket="bucket_blah", collection="coll_blah")
    assert client.session == client_clone.session
    assert client.session.server_url == client_clone.session.server_url
    assert client.session.auth == client_clone.session.auth
    assert client.session.nb_retry == client_clone.session.nb_retry
    assert client.session.retry_after == client_clone.session.retry_after
    assert client.bucket_name != client_clone.bucket_name
    assert client.collection_name != client_clone.collection_name
    assert client_clone.bucket_name == "bucket_blah"
    assert client_clone.collection_name == "coll_blah"


def test_client_clone_with_auth_and_server_url_bucket_and_collection(async_client_setup: Client):
    client = async_client_setup
    client_clone = client.clone(
        auth=("reviewer", ""),
        server_url=SERVER_URL,
        bucket="bucket_blah",
        collection="coll_blah",
    )
    assert client.session != client_clone.session
    assert client.session.server_url != client_clone.session.server_url
    assert client.session.auth != client_clone.session.auth
    assert client.bucket_name != client_clone.bucket_name
    assert client.collection_name != client_clone.collection_name
    assert client_clone.session.auth == ("reviewer", "")
    assert client_clone.session.server_url == SERVER_URL
    assert client_clone.bucket_name == "bucket_blah"
    assert client_clone.collection_name == "coll_blah"


async def test_put_is_issued_on_creation(async_client_setup: Client):
    client = async_client_setup
    await client.create_bucket(id="testbucket")
    client.session.request.assert_called_with(
        "put", "/buckets/testbucket", data=None, permissions=None, headers=DO_NOT_OVERWRITE
    )


async def test_put_is_issued_on_update(async_client_setup: Client):
    client = async_client_setup
    await client.update_bucket(
        id="testbucket",
        data={"foo": "bar", "last_modified": "1234"},
        permissions={"read": ["natim"]},
    )
    client.session.request.assert_called_with(
        "put",
        "/buckets/testbucket",
        data={"foo": "bar", "last_modified": "1234"},
        permissions={"read": ["natim"]},
        headers={"If-Match": '"1234"'},
    )


async def test_patch_is_issued_on_patch(async_client_setup: Client):
    client = async_client_setup
    await client.create_bucket(id="testbucket")
    await client.patch_bucket(
        id="testbucket", data={"foo": "bar"}, permissions={"read": ["natim"]}
    )
    client.session.request.assert_called_with(
        "patch",
        "/buckets/testbucket",
        payload={"data": {"foo": "bar"}, "permissions": {"read": ["natim"]}},
        headers={"Content-Type": "application/json"},
    )


async def test_patch_bucket_requires_patch_to_be_patch_type(async_client_setup: Client):
    client = async_client_setup
    with pytest.raises(TypeError):
        await client.patch_bucket(id="testbucket", changes=5)


async def test_update_bucket_handles_if_match(async_client_setup: Client):
    client = async_client_setup
    await client.update_bucket(id="testbucket", data={"foo": "bar"}, if_match=1234)
    client.session.request.assert_called_with(
        "put",
        "/buckets/testbucket",
        data={"foo": "bar"},
        permissions=None,
        headers={"If-Match": '"1234"'},
    )


async def test_get_is_issued_on_list_retrieval(async_client_setup: Client):
    client = async_client_setup
    await client.get_buckets()
    client.session.request.assert_called_with("get", "/buckets", headers={}, params={})


async def test_get_is_issued_on_retrieval(async_client_setup: Client):
    client = async_client_setup
    await client.get_bucket(id="testbucket")
    client.session.request.assert_called_with("get", "/buckets/testbucket", params={})


async def test_bucket_names_are_slugified(async_client_setup: Client):
    client = async_client_setup
    await client.get_bucket(id="my bucket")
    url = "/buckets/my-bucket"
    client.session.request.assert_called_with("get", url, params={})


async def test_get_bucket_supports_queryparams(async_client_setup: Client):
    client = async_client_setup
    await client.get_bucket(id="bid", _expected="123")
    url = "/buckets/bid"
    client.session.request.assert_called_with("get", url, params={"_expected": "123"})


async def test_permissions_are_retrieved(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session, permissions={"read": ["phrawzty"]})
    bucket = await client.get_bucket(id="testbucket")
    assert "phrawzty" in bucket["permissions"]["read"]


async def test_unexisting_bucket_raises(async_client_setup: Client, mocker: MockerFixture):
    client = async_client_setup
    # Make the next call to sess.request raise a 403.
    exception = KintoException()
    exception.response = mocker.MagicMock()
    exception.response.status_code = 403
    exception.request = mocker.sentinel.request
    client.session.request.side_effect = exception

    with pytest.raises(BucketNotFound) as cm:
        await client.get_bucket(id="test")
    e = cm.value
    assert e.response == exception.response
    assert e.request == mocker.sentinel.request
    assert e.message == "test"


async def test_unauthorized_raises_a_kinto_exception(
    async_client_setup: Client, mocker: MockerFixture
):
    client = async_client_setup
    # Make the next call to sess.request raise a 401.
    exception = KintoException()
    exception.response = mocker.MagicMock()
    exception.response.status_code = 401
    exception.request = mocker.sentinel.request
    client.session.request.side_effect = exception

    with pytest.raises(KintoException) as cm:
        await client.get_bucket(id="test")
    e = cm.value
    assert e.response == exception.response
    assert e.request == mocker.sentinel.request
    assert (
        e.message
        == "Unauthorized. Please authenticate or make sure the bucket can be read anonymously."
    )


async def test_http_500_raises_an_error(async_client_setup: Client, mocker: MockerFixture):
    client = async_client_setup
    exception = KintoException()
    exception.response = mocker.MagicMock()
    exception.response.status_code = 400
    exception.request = mocker.sentinel.request

    client.session.request.side_effect = exception

    try:
        await client.get_bucket(id="test")
    except KintoException as e:
        assert e.response == exception.response
        assert e.request == mocker.sentinel.request
    else:
        pytest.fail("Exception not raised")


async def test_delete_bucket_returns_the_contained_data(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session, data={"deleted": True})
    assert await client.delete_bucket(id="bucket") == {"deleted": True}


async def test_delete_bucket_handles_if_match(async_client_setup: Client):
    client = async_client_setup
    await client.delete_bucket(id="mybucket", if_match=1234)
    url = "/buckets/mybucket"
    headers = {"If-Match": '"1234"'}
    client.session.request.assert_called_with("delete", url, headers=headers)


async def test_delete_buckets_is_issued_on_list_deletion(async_client_setup: Client):
    client = async_client_setup
    await client.delete_buckets()
    client.session.request.assert_called_with("delete", "/buckets", headers=None)


async def test_get_or_create_dont_raise_in_case_of_conflict(
    async_client_setup, mocker: MockerFixture
):
    client = async_client_setup
    bucket_data = {"permissions": mocker.sentinel.permissions, "data": {"foo": "bar"}}
    client.session.request.side_effect = [get_http_error(status=412), (bucket_data, None)]
    # Should not raise.
    returned_data = await client.create_bucket(id="buck", if_not_exists=True)
    assert returned_data == bucket_data


async def test_get_or_create_bucket_raise_in_other_cases(async_client_setup: Client):
    client = async_client_setup
    client.session.request.side_effect = get_http_error(status=500)
    with pytest.raises(KintoException):
        await client.create_bucket(id="buck", if_not_exists=True)


async def test_create_bucket_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.create_bucket(data={"id": "testbucket"})
    client.session.request.assert_called_with(
        "put",
        "/buckets/testbucket",
        data={"id": "testbucket"},
        permissions=None,
        headers=DO_NOT_OVERWRITE,
    )


async def test_update_bucket_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.update_bucket(data={"id": "testbucket"})
    client.session.request.assert_called_with(
        "put", "/buckets/testbucket", data={"id": "testbucket"}, permissions=None, headers=None
    )


async def test_create_group_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.create_group(data={"id": "group"})
    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/groups/group",
        data={"id": "group"},
        permissions=None,
        headers=DO_NOT_OVERWRITE,
    )


async def test_update_group_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.update_group(data={"id": "group"})
    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/groups/group",
        data={"id": "group"},
        permissions=None,
        headers=None,
    )


async def test_patch_group_makes_request(async_client_setup: Client):
    client = async_client_setup
    await client.patch_group(id="group", data={"foo": "bar"})
    client.session.request.assert_called_with(
        "patch",
        "/buckets/mybucket/groups/group",
        payload={"data": {"foo": "bar"}},
        headers={"Content-Type": "application/json"},
    )


async def test_patch_group_requires_patch_to_be_patch_type(async_client_setup: Client):
    client = async_client_setup
    with pytest.raises(TypeError):
        await client.patch_group(id="testgroup", bucket="testbucket", changes=5)


async def test_create_group_raises_if_group_id_is_missing(async_client_setup: Client):
    client = async_client_setup
    with pytest.raises(KeyError) as e:
        await client.create_group()
    assert f"{e.value}" == "'Please provide a group id'"


async def test_update_group_raises_if_group_id_is_missing(async_client_setup: Client):
    client = async_client_setup
    with pytest.raises(KeyError) as e:
        await client.update_group()
    assert f"{e.value}" == "'Please provide a group id'"


async def test_collection_names_are_slugified(async_client_setup: Client):
    client = async_client_setup
    await client.get_collection(id="my collection")
    url = "/buckets/mybucket/collections/my-collection"
    client.session.request.assert_called_with("get", url, params={})


async def test_get_collection_supports_queryparams(async_client_setup: Client):
    client = async_client_setup
    await client.get_collection(id="cid", _expected="123")
    url = "/buckets/mybucket/collections/cid"
    client.session.request.assert_called_with("get", url, params={"_expected": "123"})


async def test_collection_creation_issues_an_http_put(
    async_client_setup: Client, mocker: MockerFixture
):
    client = async_client_setup
    await client.create_collection(id="mycollection", permissions=mocker.sentinel.permissions)

    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with(
        "put", url, data=None, permissions=mocker.sentinel.permissions, headers=DO_NOT_OVERWRITE
    )


async def test_data_can_be_sent_on_creation(async_client_setup: Client):
    client = async_client_setup
    await client.create_collection(id="mycollection", bucket="testbucket", data={"foo": "bar"})

    client.session.request.assert_called_with(
        "put",
        "/buckets/testbucket/collections/mycollection",
        data={"foo": "bar"},
        permissions=None,
        headers=DO_NOT_OVERWRITE,
    )


async def test_collection_update_issues_an_http_put(
    async_client_setup: Client, mocker: MockerFixture
):
    client = async_client_setup
    await client.update_collection(
        id="mycollection", data={"foo": "bar"}, permissions=mocker.sentinel.permissions
    )

    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with(
        "put", url, data={"foo": "bar"}, permissions=mocker.sentinel.permissions, headers=None
    )


async def test_update_handles_if_match(async_client_setup: Client):
    client = async_client_setup
    await client.update_collection(id="mycollection", data={"foo": "bar"}, if_match=1234)

    url = "/buckets/mybucket/collections/mycollection"
    headers = {"If-Match": '"1234"'}
    client.session.request.assert_called_with(
        "put", url, data={"foo": "bar"}, headers=headers, permissions=None
    )


async def test_collection_update_use_an_if_match_header(
    async_client_setup: Client, mocker: MockerFixture
):
    client = async_client_setup
    data = {"foo": "bar", "last_modified": "1234"}
    await client.update_collection(
        id="mycollection", data=data, permissions=mocker.sentinel.permissions
    )

    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with(
        "put",
        url,
        data={"foo": "bar", "last_modified": "1234"},
        permissions=mocker.sentinel.permissions,
        headers={"If-Match": '"1234"'},
    )


async def test_patch_collection_issues_an_http_patch(async_client_setup: Client):
    client = async_client_setup
    await client.patch_collection(id="mycollection", data={"key": "secret"})

    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with(
        "patch",
        url,
        payload={"data": {"key": "secret"}},
        headers={"Content-Type": "application/json"},
    )


async def test_patch_collection_handles_if_match(async_client_setup: Client):
    client = async_client_setup
    await client.patch_collection(id="mycollection", data={"key": "secret"}, if_match=1234)

    url = "/buckets/mybucket/collections/mycollection"
    headers = {"If-Match": '"1234"', "Content-Type": "application/json"}
    client.session.request.assert_called_with(
        "patch", url, payload={"data": {"key": "secret"}}, headers=headers
    )


async def test_patch_collection_requires_patch_to_be_patch_type(async_client_setup: Client):
    client = async_client_setup
    with pytest.raises(TypeError):
        await client.patch_collection(id="testcoll", bucket="testbucket", changes=5)


async def test_get_collections_returns_the_list_of_collections(async_client_setup: Client):
    client = async_client_setup
    mock_response(
        client.session,
        data=[
            {"id": "foo", "last_modified": "12345"},
            {"id": "bar", "last_modified": "59874"},
        ],
    )

    collections = await client.get_collections(bucket="default")
    assert list(collections) == [
        {"id": "foo", "last_modified": "12345"},
        {"id": "bar", "last_modified": "59874"},
    ]


async def test_collection_can_delete_all_its_records(async_client_setup: Client):
    client = async_client_setup
    await client.delete_records(bucket="abucket", collection="acollection")
    url = "/buckets/abucket/collections/acollection/records"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_delete_collections_is_issued_on_list_deletion(async_client_setup: Client):
    client = async_client_setup
    await client.delete_collections(bucket="mybucket")
    url = "/buckets/mybucket/collections"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_collection_can_be_deleted(async_client_setup: Client):
    client = async_client_setup
    data = {}
    mock_response(client.session, data=data)
    deleted = await client.delete_collection(id="mycollection")
    assert deleted == data
    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_collection_delete_if_match(async_client_setup: Client):
    client = async_client_setup
    data = {}
    mock_response(client.session, data=data)
    deleted = await client.delete_collection(id="mycollection", if_match=1234)
    assert deleted == data
    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with("delete", url, headers={"If-Match": '"1234"'})


async def test_collection_delete_if_match_not_included_if_not_safe(async_client_setup: Client):
    client = async_client_setup
    data = {}
    mock_response(client.session, data=data)
    deleted = await client.delete_collection(id="mycollection", if_match=1324, safe=False)
    assert deleted == data
    url = "/buckets/mybucket/collections/mycollection"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_get_or_create_collection_doesnt_raise_in_case_of_conflict(
    async_client_setup, mocker: MockerFixture
):
    client = async_client_setup
    data = {"permissions": mocker.sentinel.permissions, "data": {"foo": "bar"}}
    client.session.request.side_effect = [get_http_error(status=412), (data, None)]
    returned_data = await client.create_collection(
        bucket="buck", id="coll", if_not_exists=True
    )  # Should not raise.
    assert returned_data == data


async def test_get_or_create_collection_raise_in_other_cases(async_client_setup: Client):
    client = async_client_setup
    client.session.request.side_effect = get_http_error(status=500)
    with pytest.raises(KintoException):
        await client.create_collection(bucket="buck", id="coll", if_not_exists=True)


async def test_create_collection_raises_a_special_error_on_403(async_client_setup: Client):
    client = async_client_setup
    client.session.request.side_effect = get_http_error(status=403)
    with pytest.raises(KintoException) as e:
        await client.create_collection(bucket="buck", id="coll")
    expected_msg = (
        "Unauthorized. Please check that the bucket exists "
        "and that you have the permission to create or write "
        "on this collection."
    )
    assert e.value.message == expected_msg


async def test_create_collection_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.create_collection(data={"id": "coll"}, bucket="buck")
    client.session.request.assert_called_with(
        "put",
        "/buckets/buck/collections/coll",
        data={"id": "coll"},
        permissions=None,
        headers=DO_NOT_OVERWRITE,
    )


async def test_update_collection_can_deduce_id_from_data(async_client_setup: Client):
    client = async_client_setup
    await client.update_collection(data={"id": "coll"}, bucket="buck")
    client.session.request.assert_called_with(
        "put",
        "/buckets/buck/collections/coll",
        data={"id": "coll"},
        permissions=None,
        headers=None,
    )


async def test_record_id_is_given_after_creation(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data={"id": 5678})
    record = await client.create_record(data={"foo": "bar"})
    assert "id" in record["data"].keys()


async def test_generated_record_id_is_an_uuid(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.create_record(data={"foo": "bar"})
    id = client.session.request.mock_calls[0][1][1].split("/")[-1]

    uuid_regexp = r"[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}"
    assert re.match(uuid_regexp, id)


async def test_records_handles_permissions(record_async_setup: Client, mocker: MockerFixture):
    client = record_async_setup
    mock_response(client.session)
    await client.create_record(
        data={"id": "1234", "foo": "bar"}, permissions=mocker.sentinel.permissions
    )
    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/collections/mycollection/records/1234",
        data={"foo": "bar", "id": "1234"},
        permissions=mocker.sentinel.permissions,
        headers=DO_NOT_OVERWRITE,
    )


async def test_collection_argument_takes_precedence(
    record_async_setup: Client, mocker: MockerFixture
):
    client = record_async_setup
    mock_response(client.session)
    # Specify a different collection name for the client and the operation.
    client = Client(session=client.session, bucket="mybucket", collection="wrong_collection")
    await client.update_record(
        data={"id": "1234"},
        collection="good_collection",
        permissions=mocker.sentinel.permissions,
    )

    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/collections/good_collection/records/1234",
        data={"id": "1234"},
        headers=None,
        permissions=mocker.sentinel.permissions,
    )


async def test_record_id_is_derived_from_data_if_present(
    record_async_setup: Client, mocker: MockerFixture
):
    client = record_async_setup
    mock_response(client.session)
    await client.create_record(
        data={"id": "1234", "foo": "bar"}, permissions=mocker.sentinel.permissions
    )

    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/collections/mycollection/records/1234",
        data={"id": "1234", "foo": "bar"},
        permissions=mocker.sentinel.permissions,
        headers=DO_NOT_OVERWRITE,
    )


async def test_data_and_permissions_are_added_on_create(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    data = {"foo": "bar"}
    permissions = {"read": ["mle"]}

    await client.create_record(id="1234", data=data, permissions=permissions)

    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with(
        "put", url, data=data, permissions=permissions, headers=DO_NOT_OVERWRITE
    )


async def test_creation_sends_if_none_match_by_default(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    data = {"foo": "bar"}

    await client.create_record(id="1234", data=data)

    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with(
        "put", url, data=data, permissions=None, headers=DO_NOT_OVERWRITE
    )


async def test_creation_doesnt_add_if_none_match_when_overwrite(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    data = {"foo": "bar"}

    await client.create_record(id="1234", data=data, safe=False)

    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with(
        "put", url, data=data, permissions=None, headers=None
    )


async def test_records_issues_a_request_on_delete(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.delete_record(id="1234")
    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_record_issues_a_request_on_retrieval(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data={"foo": "bar"})
    record = await client.get_record(id="1234")

    assert record["data"] == {"foo": "bar"}
    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with("get", url, params={})


async def test_get_record_supports_queryparams(record_async_setup: Client):
    client = record_async_setup
    await client.get_record(id="1234", _expected="123")
    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with("get", url, params={"_expected": "123"})


async def test_collection_can_retrieve_all_records(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data=[{"id": "foo"}, {"id": "bar"}])
    records = await client.get_records()
    assert list(records) == [{"id": "foo"}, {"id": "bar"}]


async def test_collection_can_retrieve_records_timestamp(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, headers={"ETag": '"12345"'})
    timestamp = await client.get_records_timestamp()
    assert timestamp == "12345"


async def test_records_timestamp_is_cached(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data=[{"id": "foo"}, {"id": "bar"}], headers={"ETag": '"12345"'})
    await client.get_records()
    timestamp = await client.get_records_timestamp()
    assert timestamp == "12345"
    assert client.session.request.call_count == 1


async def test_records_timestamp_is_cached_per_collection(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data=[{"id": "foo"}, {"id": "bar"}], headers={"ETag": '"12345"'})
    await client.get_records(collection="foo")
    mock_response(client.session, data=[{"id": "foo"}, {"id": "bar"}], headers={"ETag": '"67890"'})
    await client.get_records(collection="bar")

    timestamp = await client.get_records_timestamp(collection="foo")
    assert timestamp == "12345"

    timestamp = await client.get_records_timestamp(collection="bar")
    assert timestamp == "67890"


async def test_pagination_is_followed(record_async_setup: Client):
    client = record_async_setup
    # Mock the calls to request.
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    client.session.request.side_effect = [
        # First one returns a list of items with a pagination token.
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        build_response(
            [{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}], {"Next-Page": link}
        ),
        # Second one returns a list of items without a pagination token.
        build_response([{"id": "5", "value": "item5"}, {"id": "6", "value": "item6"}]),
    ]
    records = await client.get_records(bucket="bucket", collection="collection")

    assert list(records) == [
        {"id": "1", "value": "item1"},
        {"id": "2", "value": "item2"},
        {"id": "3", "value": "item3"},
        {"id": "4", "value": "item4"},
        {"id": "5", "value": "item5"},
        {"id": "6", "value": "item6"},
    ]


async def test_pagination_is_followed_generator(record_async_setup: Client):
    client = record_async_setup
    # Mock the calls to request.
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    response = [
        # First one returns a list of items with a pagination token.
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        build_response(
            [{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}], {"Next-Page": link}
        ),
        # Second one returns a list of items without a pagination token.
        build_response([{"id": "5", "value": "item5"}, {"id": "6", "value": "item6"}]),
    ]

    client.session.request.side_effect = response

    # Build repsonses for assertion without next page
    response = [record[0] for record in response]

    for index, page_records in enumerate(await client.get_paginated_records()):
        assert response[index] == page_records


async def test_pagination_is_followed_for_number_of_pages(record_async_setup: Client):
    client = record_async_setup
    # Mock the calls to request.
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    client.session.request.side_effect = [
        # First one returns a list of items with a pagination token.
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        build_response(
            [{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}], {"Next-Page": link}
        ),
        # Second one returns a list of items without a pagination token.
        build_response([{"id": "5", "value": "item5"}, {"id": "6", "value": "item6"}]),
    ]
    records = await client.get_records(bucket="bucket", collection="collection", pages=2)

    assert list(records) == [
        {"id": "1", "value": "item1"},
        {"id": "2", "value": "item2"},
        {"id": "3", "value": "item3"},
        {"id": "4", "value": "item4"},
    ]


async def test_pagination_is_not_followed_if_limit_is_specified(record_async_setup: Client):
    client = record_async_setup
    # Mock the calls to request.
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    client.session.request.side_effect = [
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        build_response([{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}]),
    ]
    records = await client.get_records(bucket="bucket", collection="collection", _limit=2)

    assert list(records) == [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}]


async def test_pagination_supports_if_none_match(record_async_setup: Client):
    client = record_async_setup
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    client.session.request.side_effect = [
        # First one returns a list of items with a pagination token.
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        # Second one returns a list of items without a pagination token.
        build_response([{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}]),
    ]
    await client.get_records(bucket="bucket", collection="collection", if_none_match="1234")

    # Check that the If-None-Match header is present in the requests.
    client.session.request.assert_any_call(
        "get",
        "/buckets/bucket/collections/collection/records",
        headers={"If-None-Match": '"1234"'},
        params={},
    )
    client.session.request.assert_any_call(
        "get", link, headers={"If-None-Match": '"1234"'}, params={}
    )


async def test_pagination_generator_if_none_match(record_async_setup: Client):
    client = record_async_setup
    link = "http://example.org/buckets/buck/collections/coll/records/?token=1234"

    response = [
        # First one returns a list of items with a pagination token.
        build_response(
            [{"id": "1", "value": "item1"}, {"id": "2", "value": "item2"}], {"Next-Page": link}
        ),
        build_response(
            [{"id": "3", "value": "item3"}, {"id": "4", "value": "item4"}], {"Next-Page": link}
        ),
        # Second one returns a list of items without a pagination token.
        build_response([{"id": "5", "value": "item5"}, {"id": "6", "value": "item6"}]),
    ]

    client.session.request.side_effect = response

    # Build repsonses for assertion without next page
    response = [record[0] for record in response]

    for index, page_records in enumerate(await client.get_paginated_records(if_none_match="1234")):
        # Check that the If-None-Match header is present in the requests.
        assert response[index] == page_records

    # Check that the If-None-Match header is present in the requests.
    client.session.request.assert_any_call(
        "get", link, headers={"If-None-Match": '"1234"'}, params={}
    )


async def test_collection_can_delete_a_record(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session, data={"id": 1234})
    resp = await client.delete_record(id=1234)
    assert resp == {"id": 1234}
    url = "/buckets/mybucket/collections/mycollection/records/1234"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_record_delete_if_match(record_async_setup: Client):
    client = record_async_setup
    data = {}
    mock_response(client.session, data=data)
    deleted = await client.delete_record(
        collection="mycollection", bucket="mybucket", id="1", if_match=1234
    )
    assert deleted == data
    url = "/buckets/mybucket/collections/mycollection/records/1"
    client.session.request.assert_called_with("delete", url, headers={"If-Match": '"1234"'})


async def test_record_delete_if_match_not_included_if_not_safe(record_async_setup: Client):
    client = record_async_setup
    data = {}
    mock_response(client.session, data=data)
    deleted = await client.delete_record(
        collection="mycollection", bucket="mybucket", id="1", if_match=1234, safe=False
    )
    assert deleted == data
    url = "/buckets/mybucket/collections/mycollection/records/1"
    client.session.request.assert_called_with("delete", url, headers=None)


async def test_update_record_gets_the_id_from_data_if_exists(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.update_record(
        bucket="mybucket", collection="mycollection", data={"id": 1, "foo": "bar"}
    )

    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/collections/mycollection/records/1",
        data={"id": 1, "foo": "bar"},
        headers=None,
        permissions=None,
    )


async def test_update_record_handles_if_match(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.update_record(
        bucket="mybucket",
        collection="mycollection",
        data={"id": 1, "foo": "bar"},
        if_match=1234,
    )

    headers = {"If-Match": '"1234"'}
    client.session.request.assert_called_with(
        "put",
        "/buckets/mybucket/collections/mycollection/records/1",
        data={"id": 1, "foo": "bar"},
        headers=headers,
        permissions=None,
    )


async def test_patch_record_uses_the_patch_method(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.patch_record(
        bucket="mybucket", collection="mycollection", data={"id": 1, "foo": "bar"}
    )

    client.session.request.assert_called_with(
        "patch",
        "/buckets/mybucket/collections/mycollection/records/1",
        payload={"data": {"id": 1, "foo": "bar"}},
        headers={"Content-Type": "application/json"},
    )


async def test_patch_record_recognizes_patchtype(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.patch_record(
        bucket="mybucket",
        collection="mycollection",
        changes=MergePatch({"foo": "bar"}, {"read": ["alice"]}),
        id=1,
    )

    client.session.request.assert_called_with(
        "patch",
        "/buckets/mybucket/collections/mycollection/records/1",
        payload={"data": {"foo": "bar"}, "permissions": {"read": ["alice"]}},
        headers={"Content-Type": "application/merge-patch+json"},
    )


async def test_patch_record_understands_jsonpatch(record_async_setup: Client):
    client = record_async_setup
    mock_response(client.session)
    await client.patch_record(
        bucket="mybucket",
        collection="mycollection",
        changes=JSONPatch([{"op": "add", "patch": "/baz", "value": "qux"}]),
        id=1,
    )

    client.session.request.assert_called_with(
        "patch",
        "/buckets/mybucket/collections/mycollection/records/1",
        payload=[{"op": "add", "patch": "/baz", "value": "qux"}],
        headers={"Content-Type": "application/json-patch+json"},
    )


async def test_patch_record_requires_data_to_be_patch_type(record_async_setup: Client):
    client = record_async_setup
    with pytest.raises(TypeError, match="couldn't understand patch body 5"):
        await client.patch_record(id=1, collection="testcoll", bucket="testbucket", changes=5)


async def test_patch_record_requires_id(record_async_setup: Client):
    client = record_async_setup
    with pytest.raises(KeyError, match="Unable to patch record, need an id."):
        await client.patch_record(collection="testcoll", bucket="testbucket", data={})


async def test_update_record_raises_if_no_id_is_given(record_async_setup: Client):
    client = record_async_setup
    with pytest.raises(KeyError) as cm:
        await client.update_record(
            data={"foo": "bar"},  # Omit the id on purpose here.
            bucket="mybucket",
            collection="mycollection",
        )
    assert str(cm.value) == "'Unable to update a record, need an id.'"


async def test_get_or_create_record_doesnt_raise_in_case_of_conflict(
    record_async_setup, mocker: MockerFixture
):
    client = record_async_setup
    data = {"permissions": mocker.sentinel.permissions, "data": {"foo": "bar"}}
    client.session.request.side_effect = [get_http_error(status=412), (data, None)]
    returned_data = await client.create_record(
        bucket="buck", collection="coll", data={"id": 1234, "foo": "bar"}, if_not_exists=True
    )  # Should not raise.
    assert returned_data == data


async def test_get_or_create_record_raise_in_other_cases(record_async_setup: Client):
    client = record_async_setup
    client.session.request.side_effect = get_http_error(status=500)
    with pytest.raises(KintoException):
        await client.create_record(
            bucket="buck",
            collection="coll",
            data={"foo": "bar"},
            id="record",
            if_not_exists=True,
        )


async def test_create_record_raises_a_special_error_on_403(record_async_setup: Client):
    client = record_async_setup
    client.session.request.side_effect = get_http_error(status=403)
    with pytest.raises(KintoException) as e:
        await client.create_record(bucket="buck", collection="coll", data={"foo": "bar"})
    expected_msg = (
        "Unauthorized. Please check that the collection exists"
        " and that you have the permission to create or write "
        "on this collection record."
    )
    assert e.value.message == expected_msg


async def test_create_record_can_deduce_id_from_data(record_async_setup: Client):
    client = record_async_setup
    await client.create_record(data={"id": "record"}, bucket="buck", collection="coll")
    client.session.request.assert_called_with(
        "put",
        "/buckets/buck/collections/coll/records/record",
        data={"id": "record"},
        permissions=None,
        headers=DO_NOT_OVERWRITE,
    )


async def test_update_record_can_deduce_id_from_data(record_async_setup: Client):
    client = record_async_setup
    await client.update_record(data={"id": "record"}, bucket="buck", collection="coll")
    client.session.request.assert_called_with(
        "put",
        "/buckets/buck/collections/coll/records/record",
        data={"id": "record"},
        permissions=None,
        headers=None,
    )


async def test_basic_retrivial_of_bucket_history(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session)
    await client.get_history(bucket="mybucket")
    url = "/buckets/mybucket/history"
    client.session.request.assert_called_with("get", url, headers={}, params={})


async def test_filter_sorting_operations_on_bucket_history(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session)
    await client.get_history(
        bucket="mybucket", _limit=2, _sort="-last_modified", _since="1533762576015"
    )

    url = "/buckets/mybucket/history"
    client.session.request.assert_called_with(
        "get",
        url,
        headers={},
        params={"_limit": 2, "_sort": "-last_modified", "_since": "1533762576015"},
    )


async def test_filtering_by_resource_name(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session)
    await client.get_history(bucket="mybucket", resource_name="collection")
    url = "/buckets/mybucket/history"
    client.session.request.assert_called_with(
        "get", url, headers={}, params={"resource_name": "collection"}
    )


async def test_purging_of_history(async_client_setup: Client):
    client = async_client_setup
    mock_response(client.session)
    await client.purge_history(bucket="mybucket")
    url = "/buckets/mybucket/history"
    client.session.request.assert_called_with("delete", url, headers=None)

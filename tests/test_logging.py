from kinto_http import Client
from pytest_mock.plugin import MockerFixture


def test_create_bucket_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck", data={"foo": "bar"})
    mocked_logger.info.assert_called_with("Create bucket 'buck'")


def test_update_bucket_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.update_bucket(id="buck", data={"foo": "bar"})
    mocked_logger.info.assert_called_with("Update bucket 'buck'")


def test_patch_bucket_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.patch_bucket(id="buck", data={"foo": "bar"})
    mocked_logger.info.assert_called_with("Patch bucket 'buck'")


def test_get_bucket_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.get_bucket(id="buck")
    mocked_logger.info.assert_called_with("Get bucket 'buck'")


def test_delete_bucket_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_bucket(id="buck")
    mocked_logger.info.assert_called_with("Delete bucket 'buck'")


def test_delete_buckets_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_buckets()
    mocked_logger.info.assert_called_with("Delete buckets")


def test_create_group_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_group(
        id="mozilla", bucket="buck", data={"foo": "bar"}, permissions={"write": ["blah"]}
    )
    mocked_logger.info.assert_called_with("Create group 'mozilla' in bucket 'buck'")


def test_update_group_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.update_group(
        data={"foo": "bar"},
        id="mozilla",
        bucket="buck",
        permissions={"write": ["blahblah"]},
    )
    mocked_logger.info.assert_called_with("Update group 'mozilla' in bucket 'buck'")


def test_patch_group_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.patch_group(
        data={"foo": "bar"},
        id="mozilla",
        bucket="buck",
        permissions={"write": ["blahblah"]},
    )
    mocked_logger.info.assert_called_with("Patch group 'mozilla' in bucket 'buck'")


def test_get_group_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.get_group(id="mozilla", bucket="buck")
    mocked_logger.info.assert_called_with("Get group 'mozilla' in bucket 'buck'")


def test_delete_group_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_group(id="mozilla", bucket="buck")
    mocked_logger.info.assert_called_with("Delete group 'mozilla' in bucket 'buck'")


def test_delete_groups_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_groups(bucket="buck")
    mocked_logger.info.assert_called_with("Delete groups in bucket 'buck'")


def test_create_collection_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_collection(
        id="mozilla", bucket="buck", data={"foo": "bar"}, permissions={"write": ["blah"]}
    )
    mocked_logger.info.assert_called_with("Create collection 'mozilla' in bucket 'buck'")


def test_update_collection_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.update_collection(
        data={"foo": "bar"},
        id="mozilla",
        bucket="buck",
        permissions={"write": ["blahblah"]},
    )
    mocked_logger.info.assert_called_with("Update collection 'mozilla' in bucket 'buck'")


def test_patch_collection_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.patch_collection(
        data={"foo": "bar"},
        id="mozilla",
        bucket="buck",
        permissions={"write": ["blahblah"]},
    )
    mocked_logger.info.assert_called_with("Patch collection 'mozilla' in bucket 'buck'")


def test_get_collection_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.get_collection(id="mozilla", bucket="buck")
    mocked_logger.info.assert_called_with("Get collection 'mozilla' in bucket 'buck'")


def test_delete_collection_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_collection(id="mozilla", bucket="buck")
    mocked_logger.info.assert_called_with("Delete collection 'mozilla' in bucket 'buck'")


def test_delete_collections_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.delete_collections(bucket="buck")
    mocked_logger.info.assert_called_with("Delete collections in bucket 'buck'")


def test_create_record_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(id="mozilla", bucket="buck")
    client_setup.create_record(
        id="fake-record",
        data={"foo": "bar"},
        permissions={"write": ["blah"]},
        bucket="buck",
        collection="mozilla",
    )
    mocked_logger.info.assert_called_with(
        "Create record with id 'fake-record' in collection 'mozilla' in bucket 'buck'"
    )


def test_update_record_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(bucket="buck", id="mozilla")
    client_setup.update_record(
        id="fake-record", data={"ss": "aa"}, bucket="buck", collection="mozilla"
    )
    mocked_logger.info.assert_called_with(
        "Update record with id 'fake-record' in collection 'mozilla' in bucket 'buck'"
    )


def test_patch_record_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(bucket="buck", id="mozilla")
    client_setup.patch_record(
        id="fake-record", data={"ss": "aa"}, bucket="buck", collection="mozilla"
    )
    mocked_logger.info.assert_called_with(
        "Patch record with id 'fake-record' in collection 'mozilla' in bucket 'buck'"
    )


def test_get_record_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(id="mozilla", bucket="buck")
    client_setup.get_record(id="fake-record", bucket="buck", collection="mozilla")
    mocked_logger.info.assert_called_with(
        "Get record with id 'fake-record' from collection 'mozilla' in bucket 'buck'"
    )


def test_delete_record_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(id="mozilla", bucket="buck")
    client_setup.delete_record(id="fake-record", bucket="buck", collection="mozilla")
    mocked_logger.info.assert_called_with(
        "Delete record with id 'fake-record' from collection 'mozilla' in bucket 'buck'"
    )


def test_delete_records_logs_info_message(client_setup: Client, mocker: MockerFixture):
    mocked_logger = mocker.patch("kinto_http.client.logger")
    client_setup.create_bucket(id="buck")
    client_setup.create_collection(id="mozilla", bucket="buck")
    client_setup.delete_records(bucket="buck", collection="mozilla")
    mocked_logger.info.assert_called_with(
        "Delete records from collection 'mozilla' in bucket 'buck'"
    )

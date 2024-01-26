from pytest_mock import MockerFixture

from kinto_http import Client, exceptions
from kinto_http.replication import replicate

from .support import mock_response


def test_destination_bucket_is_created_if_not_exist(mocker: MockerFixture):
    destination = mocker.MagicMock()
    origin = mocker.MagicMock()
    destination.get_bucket.side_effect = exceptions.BucketNotFound
    replicate(origin, destination)
    destination.create_bucket.assert_called_with(if_not_exists=True)


def test_destination_collection_is_created_if_not_exist(mocker: MockerFixture):
    destination = mocker.MagicMock()
    origin = mocker.MagicMock()
    destination.get_collection.side_effect = exceptions.KintoException
    origin.get_collection.return_value = {
        "data": mocker.sentinel.data,
        "permissions": mocker.sentinel.permissions,
    }
    replicate(origin, destination)
    destination.create_collection.assert_called_with(
        data=mocker.sentinel.data, permissions=mocker.sentinel.permissions, if_not_exists=True
    )


def test_new_records_are_sent_to_the_destination(mocker: MockerFixture):
    destination = mocker.MagicMock()
    origin = mocker.MagicMock()
    origin.get_records.return_value = [
        {"id": "1234", "foo": "bar", "last_modified": 1234},
        {"id": "4567", "bar": "baz", "last_modified": 4567},
    ]
    batch = mocker.MagicMock()
    batched = batch().__enter__()
    destination.batch = batch

    replicate(origin, destination)
    batched.update_record.assert_any_call(
        data={"id": "4567", "bar": "baz", "last_modified": 4567}, safe=False
    )
    batched.update_record.assert_any_call(
        data={"id": "1234", "foo": "bar", "last_modified": 1234}, safe=False
    )


def test_removed_records_are_deleted_on_the_destination(mocker: MockerFixture):
    destination = mocker.MagicMock()
    origin = mocker.MagicMock()
    origin.get_records.return_value = [
        {"id": "1234", "deleted": True, "last_modified": "1234"},
        {"id": "4567", "deleted": True, "last_modified": "4567"},
    ]
    batch = mocker.MagicMock()
    batched = batch().__enter__()
    destination.batch = batch

    replicate(origin, destination)
    batched.delete_record.assert_any_call("1234", last_modified="1234")
    batched.delete_record.assert_any_call("4567", last_modified="4567")


def test_logger_outputs_replication_information(mocker: MockerFixture):
    logger = mocker.patch("kinto_http.replication.logger")
    origin_session = mocker.MagicMock()
    origin_session.server_url = "http://origin/v1"
    destination_session = mocker.MagicMock()
    destination_session.server_url = "http://destination/v1"
    mock_response(origin_session)
    mock_response(destination_session)

    origin = Client(session=origin_session, bucket="buck", collection="coll")
    destination = Client(session=destination_session, bucket="buck", collection="coll")
    destination._server_settings = {"batch_max_requests": 15}
    replicate(origin, destination)
    msg = (
        "Replication from <KintoClient http://origin/v1/buckets/buck/"
        "collections/coll> to <KintoClient http://destination/v1/"
        "buckets/buck/collections/coll>"
    )
    logger.info.assert_any_call(msg)
    logger.info.assert_any_call("replication of 0 records")

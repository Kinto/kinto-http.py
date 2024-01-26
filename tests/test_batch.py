import pytest
from kinto_http import Client
from kinto_http.batch import BatchSession
from kinto_http.exceptions import KintoException
from pytest_mock.plugin import MockerFixture


def test_requests_are_stacked(batch_setup: Client, mocker: MockerFixture):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/foobar/baz", mocker.sentinel.data, mocker.sentinel.permissions)
    assert len(batch.requests) == 1


def test_send_adds_data_attribute(batch_setup: Client):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/foobar/baz", data={"foo": "bar"})
    batch.send()

    batch_setup.session.request.assert_called_with(
        method="POST",
        endpoint=batch_setup.endpoints.get("batch"),
        payload={
            "requests": [
                {"method": "GET", "path": "/foobar/baz", "body": {"data": {"foo": "bar"}}}
            ]
        },
    )


def test_send_adds_permissions_attribute(batch_setup: Client, mocker: MockerFixture):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/foobar/baz", permissions=mocker.sentinel.permissions)
    batch.send()

    batch_setup.session.request.assert_called_with(
        method="POST",
        endpoint=batch_setup.endpoints.get("batch"),
        payload={
            "requests": [
                {
                    "method": "GET",
                    "path": "/foobar/baz",
                    "body": {"permissions": mocker.sentinel.permissions},
                }
            ]
        },
    )


def test_send_adds_headers_if_specified(batch_setup: Client):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/foobar/baz", headers={"Foo": "Bar"})
    batch.send()

    batch_setup.session.request.assert_called_with(
        method="POST",
        endpoint=batch_setup.endpoints.get("batch"),
        payload={
            "requests": [
                {"method": "GET", "path": "/foobar/baz", "headers": {"Foo": "Bar"}, "body": {}}
            ]
        },
    )


def test_batch_send_multiple_requests_if_too_many_requests(batch_setup: Client):
    batch = BatchSession(batch_setup, batch_max_requests=3)
    for i in range(5):
        batch.request("GET", "/foobar/%s" % i)
    batch.send()

    calls = batch_setup.session.request.call_args_list
    assert len(calls) == 2
    _, kwargs1 = calls[0]
    assert kwargs1["payload"]["requests"][-1]["path"] == "/foobar/2"
    _, kwargs2 = calls[1]
    assert kwargs2["payload"]["requests"][0]["path"] == "/foobar/3"


def test_reset_empties_the_requests_cache(batch_setup: Client, mocker: MockerFixture):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/foobar/baz", permissions=mocker.sentinel.permissions)
    assert len(batch.requests) == 1
    batch.reset()
    assert len(batch.requests) == 0


def test_prefix_is_removed_from_batch_requests(batch_setup: Client):
    batch = BatchSession(batch_setup)
    batch.request("GET", "/v1/foobar")
    batch.send()

    calls = batch_setup.session.request.call_args_list
    _, kwargs1 = calls[0]
    assert kwargs1["payload"]["requests"][0]["path"] == "/foobar"


def test_batch_raises_exception_as_soon_as_subrequest_fails_with_status_code_5xx(
    batch_setup: Client, mocker: MockerFixture
):
    batch_setup.session.request.side_effect = [
        (
            {
                "responses": [
                    {
                        "status": 502,
                        "path": "/url2",
                        "body": {"message": "Host not reachable"},
                        "headers": {},
                    }
                ]
            },
            mocker.sentinel.headers,
        ),
        (
            {"responses": [{"status": 200, "path": "/url1", "body": {}, "headers": {}}]},
            mocker.sentinel.headers,
        ),
    ]

    batch = BatchSession(batch_setup, batch_max_requests=1)
    batch.request("GET", "/v1/foobar")
    batch.request("GET", "/v1/foobar")

    with pytest.raises(KintoException):
        batch.send()
    assert batch_setup.session.request.call_count == 1


def test_parse_results_retrieves_response_data(batch_setup: Client, mocker: MockerFixture):
    batch_response = {"body": {"data": {"id": "hey"}}, "status": 200}
    mocker.sentinel.resp = {"responses": [batch_response]}
    batch_setup.session.request.return_value = (mocker.sentinel.resp, mocker.sentinel.headers)
    batch = BatchSession(batch_setup)
    batch.request("GET", "/v1/foobar")
    batch.send()

    results = batch.results()
    assert len(results) == 1
    assert results[0] == batch_response["body"]

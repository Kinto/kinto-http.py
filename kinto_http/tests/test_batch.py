import unittest
from unittest import mock

from kinto_http.batch import BatchSession
from kinto_http.exceptions import KintoException


class BatchRequestsTest(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        mock.sentinel.resp = {"responses": []}
        self.client.session.request.return_value = (mock.sentinel.resp, mock.sentinel.headers)

    def test_requests_are_stacked(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/foobar/baz", mock.sentinel.data, mock.sentinel.permissions)
        assert len(batch.requests) == 1

    def test_send_adds_data_attribute(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/foobar/baz", data={"foo": "bar"})
        batch.send()

        self.client.session.request.assert_called_with(
            method="POST",
            endpoint=self.client.endpoints.get("batch"),
            payload={
                "requests": [
                    {"method": "GET", "path": "/foobar/baz", "body": {"data": {"foo": "bar"}}}
                ]
            },
        )

    def test_send_adds_permissions_attribute(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/foobar/baz", permissions=mock.sentinel.permissions)
        batch.send()

        self.client.session.request.assert_called_with(
            method="POST",
            endpoint=self.client.endpoints.get("batch"),
            payload={
                "requests": [
                    {
                        "method": "GET",
                        "path": "/foobar/baz",
                        "body": {"permissions": mock.sentinel.permissions},
                    }
                ]
            },
        )

    def test_send_adds_headers_if_specified(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/foobar/baz", headers={"Foo": "Bar"})
        batch.send()

        self.client.session.request.assert_called_with(
            method="POST",
            endpoint=self.client.endpoints.get("batch"),
            payload={
                "requests": [
                    {"method": "GET", "path": "/foobar/baz", "headers": {"Foo": "Bar"}, "body": {}}
                ]
            },
        )

    def test_batch_send_multiple_requests_if_too_many_requests(self):
        batch = BatchSession(self.client, batch_max_requests=3)
        for i in range(5):
            batch.request("GET", "/foobar/%s" % i)
        batch.send()

        calls = self.client.session.request.call_args_list
        assert len(calls) == 2
        _, kwargs1 = calls[0]
        assert kwargs1["payload"]["requests"][-1]["path"] == "/foobar/2"
        _, kwargs2 = calls[1]
        assert kwargs2["payload"]["requests"][0]["path"] == "/foobar/3"

    def test_reset_empties_the_requests_cache(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/foobar/baz", permissions=mock.sentinel.permissions)
        assert len(batch.requests) == 1
        batch.reset()
        assert len(batch.requests) == 0

    def test_prefix_is_removed_from_batch_requests(self):
        batch = BatchSession(self.client)
        batch.request("GET", "/v1/foobar")
        batch.send()

        calls = self.client.session.request.call_args_list
        _, kwargs1 = calls[0]
        assert kwargs1["payload"]["requests"][0]["path"] == "/foobar"

    def test_batch_raises_exception_as_soon_as_subrequest_fails_with_status_code_5xx(self):
        self.client.session.request.side_effect = [
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
                mock.sentinel.headers,
            ),
            (
                {"responses": [{"status": 200, "path": "/url1", "body": {}, "headers": {}}]},
                mock.sentinel.headers,
            ),
        ]

        batch = BatchSession(self.client, batch_max_requests=1)
        batch.request("GET", "/v1/foobar")
        batch.request("GET", "/v1/foobar")

        with self.assertRaises(KintoException):
            batch.send()
        assert self.client.session.request.call_count == 1

    def test_parse_results_retrieves_response_data(self):
        batch_response = {"body": {"data": {"id": "hey"}}, "status": 200}
        mock.sentinel.resp = {"responses": [batch_response]}
        self.client.session.request.return_value = (mock.sentinel.resp, mock.sentinel.headers)
        batch = BatchSession(self.client)
        batch.request("GET", "/v1/foobar")
        batch.send()

        results = batch.results()
        assert len(results) == 1
        assert results[0] == batch_response["body"]

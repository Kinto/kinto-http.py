import unittest2 as unittest
import mock

from kinto_client import Client
from kinto_client.batch import Batch


class BatchRequestsTest(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        self.client.session.request.return_value = (mock.sentinel.resp,
                                                    mock.sentinel.headers)

    def test_requests_are_stacked(self):
        batch = Batch(self.client)
        batch.request('GET', '/foobar/baz',
                      mock.sentinel.data,
                      mock.sentinel.permissions)
        assert len(batch.requests) == 1

    def test_send_adds_data_attribute(self):
        batch = Batch(self.client)
        batch.request('GET', '/foobar/baz', data={'foo': 'bar'})
        batch.send()

        self.client.session.request.assert_called_with(
            'POST',
            self.client.endpoints.get('batch'),
            payload={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'body': {'data': {'foo': 'bar'}}
            }]}
        )

    def test_send_adds_permissions_attribute(self):
        batch = Batch(self.client)
        batch.request('GET', '/foobar/baz',
                      permissions=mock.sentinel.permissions)
        batch.send()

        self.client.session.request.assert_called_with(
            'POST',
            self.client.endpoints.get('batch'),
            payload={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'body': {'permissions': mock.sentinel.permissions}
            }]}
        )

    def test_send_adds_headers_if_specified(self):
        batch = Batch(self.client)
        batch.request('GET', '/foobar/baz', headers={'Foo': 'Bar'})
        batch.send()

        self.client.session.request.assert_called_with(
            'POST',
            self.client.endpoints.get('batch'),
            payload={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'headers': {'Foo': 'Bar'},
                'body': {}
            }]}
        )

    def test_batch_send_multiple_requests_if_too_many_requests(self):
        batch = Batch(self.client, batch_max_requests=3)
        for i in range(5):
            batch.request('GET', '/foobar/%s' % i)
        batch.send()

        calls = self.client.session.request.call_args_list
        assert len(calls) == 2
        _, kwargs1 = calls[0]
        assert kwargs1['payload']['requests'][-1]['path'] == '/foobar/2'
        _, kwargs2 = calls[1]
        assert kwargs2['payload']['requests'][0]['path'] == '/foobar/3'

    def test_reset_empties_the_requests_cache(self):
        batch = Batch(self.client)
        batch.request('GET', '/foobar/baz',
                      permissions=mock.sentinel.permissions)
        assert len(batch.requests) == 1
        batch.reset()
        assert len(batch.requests) == 0

    def test_prefix_is_removed_from_batch_requests(self):
        batch = Batch(self.client)
        batch.request('GET', '/v1/foobar')
        batch.send()

        calls = self.client.session.request.call_args_list
        _, kwargs1 = calls[0]
        assert kwargs1['payload']['requests'][0]['path'] == '/foobar'


class RetryBatchTest(unittest.TestCase):

    def setUp(self):
        self.client = Client('https://server.com')
        patch = mock.patch('kinto_client.requests.request')
        self.addCleanup(patch.stop)
        self.request_mocked = patch.start()

        self.response_200 = mock.MagicMock()
        self.response_200.status_code = 200
        self.response_200.json().return_value = mock.sentinel.resp,
        self.response_200.headers = mock.sentinel.headers

        body_503 = {
            "message": "Service temporary unavailable due to overloading",
            "code": 503,
            "error": "Service Unavailable",
            "errno": 201
        }
        headers_503 = {
            "Retry-After": 30,
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": 151
        }
        self.response_503 = mock.MagicMock()
        self.response_503.status_code = 503
        self.response_503.json.return_value = body_503
        self.response_503.headers = headers_503

        self.request_mocked.side_effect = [self.response_503]

    def test_batch_does_not_retry_by_default(self):
        batch = Batch(self.client)
        batch.request('GET', '/v1/foobar')
        with self.assertRaises(Exception):
            batch.send()

    def test_batch_can_retry_several_times(self):
        self.request_mocked.side_effect = [self.response_503,
                                           self.response_503,  # retry 1
                                           self.response_200]  # retry 2

        batch = Batch(self.client, retry=2)
        batch.request('GET', '/v1/foobar')
        batch.send()

    def test_batch_fails_if_retry_exhausted(self):
        self.request_mocked.side_effect = [self.response_503,
                                           self.response_503,  # retry 1
                                           self.response_503,  # retry 2
                                           self.response_200]

        batch = Batch(self.client, retry=2)
        batch.request('GET', '/v1/foobar')
        with self.assertRaises(Exception):
            batch.send()

    def test_waits_if_retry_after_header_is_present(self):
        pass

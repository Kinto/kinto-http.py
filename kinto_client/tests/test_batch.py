import unittest2 as unittest
import mock

from kinto_client.batch import Session


class SessionRequestsTest(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        self.client.session.request.return_value = (mock.sentinel.resp,
                                                    mock.sentinel.headers)

    def test_requests_are_stacked(self):
        batch = Session(self.client)
        batch.request('GET', '/foobar/baz',
                      mock.sentinel.data,
                      mock.sentinel.permissions)
        assert len(batch.requests) == 1

    def test_send_adds_data_attribute(self):
        batch = Session(self.client)
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
        batch = Session(self.client)
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
        batch = Session(self.client)
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
        batch = Session(self.client, batch_max_requests=3)
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
        batch = Session(self.client)
        batch.request('GET', '/foobar/baz',
                      permissions=mock.sentinel.permissions)
        assert len(batch.requests) == 1
        batch.reset()
        assert len(batch.requests) == 0

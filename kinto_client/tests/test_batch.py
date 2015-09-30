import unittest2 as unittest
import mock

from kinto_client.batch import Batch, batch_requests


class BatchRequestsTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.endpoints = mock.MagicMock()

    def test_requests_are_stacked(self):
        batch = Batch(self.session, self.endpoints)
        batch.add('GET', '/foobar/baz',
                  mock.sentinel.data,
                  mock.sentinel.permissions)
        assert len(batch.requests) == 1

    def test_send_adds_data_attribute(self):
        batch = Batch(self.session, self.endpoints)
        batch.add('GET', '/foobar/baz', data={'foo': 'bar'})
        batch.send()

        self.session.request.assert_called_with(
            'POST',
            self.endpoints.batch(),
            data={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'body': {'data': {'foo': 'bar'}}
            }]}
        )

    def test_send_adds_permissions_attribute(self):
        batch = Batch(self.session, self.endpoints)
        batch.add('GET', '/foobar/baz', permissions=mock.sentinel.permissions)
        batch.send()

        self.session.request.assert_called_with(
            'POST',
            self.endpoints.batch(),
            data={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'body': {'permissions': mock.sentinel.permissions}
            }]}
        )

    def test_send_adds_headers_if_specified(self):
        batch = Batch(self.session, self.endpoints)
        batch.add('GET', '/foobar/baz', headers={'Foo': 'Bar'})
        batch.send()

        self.session.request.assert_called_with(
            'POST',
            self.endpoints.batch(),
            data={'requests': [{
                'method': 'GET',
                'path': '/foobar/baz',
                'headers': {'Foo': 'Bar'},
                'body': {}
            }]}
        )

    def test_send_empties_the_requests_cache(self):
        batch = Batch(self.session, self.endpoints)
        batch.add('GET', '/foobar/baz', permissions=mock.sentinel.permissions)
        assert len(batch.requests) == 1
        batch.send()
        assert len(batch.requests) == 0

    def test_context_manager_works_as_expected(self):
        batcher = batch_requests
        with batcher(self.session, self.endpoints) as batch:
            batch.add('PUT', '/records/1234', data={'foo': 'bar'})
            batch.add('PUT', '/records/5678', data={'bar': 'baz'})

        assert self.session.request.called

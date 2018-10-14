import pkg_resources
import pytest
import sys
import time
import unittest
from unittest import mock

from kinto_http.session import Session, create_session
from kinto_http.exceptions import KintoException, BackoffException
from kinto_http.session import USER_AGENT
from .support import get_200, get_503, get_403, get_http_response


def fake_response(status_code):
    response = mock.MagicMock()
    response.headers = {'User-Agent': USER_AGENT}
    response.status_code = status_code
    return response


class SessionTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch('kinto_http.session.requests')
        self.requests_mock = p.start()
        self.addCleanup(p.stop)

    def test_uses_specified_server_url(self):
        session = Session(mock.sentinel.server_url)
        self.assertEqual(session.server_url, mock.sentinel.server_url)

    def test_no_auth_is_used_by_default(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        self.assertEqual(session.auth, None)
        session.request('get', '/test')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            headers=self.requests_mock.request.return_value.headers)

    def test_bad_http_status_raises_exception(self):
        response = fake_response(400)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')

        self.assertRaises(KintoException, session.request, 'get', '/test',
                          headers=self.requests_mock.request.return_value.headers)

    def test_bad_http_status_raises_exception_even_in_case_of_invalid_json_response(self):
        response = fake_response(502)
        response.json.side_effect = ValueError
        response.text = "Foobar"
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')

        with pytest.raises(KintoException) as e:
            session.request('get', '/test')
        self.assertEqual(e.value.message, "502 - Foobar")

    def test_session_injects_auth_on_requests(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session(auth=mock.sentinel.auth,
                          server_url='https://example.org')
        session.request('get', '/test')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            auth=mock.sentinel.auth, headers=self.requests_mock.request.return_value.headers)

    def test_requests_arguments_are_forwarded(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', '/test',
                        foo=mock.sentinel.bar)
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test',
            foo=mock.sentinel.bar, headers=self.requests_mock.request.return_value.headers)

    def test_raises_exception_if_headers_not_dict(self):
        session = Session('https://example.org')

        with pytest.raises(TypeError):
            session.request('get', '/test', headers=4)

    def test_passed_data_is_encoded_to_json(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('post', '/test',
                        data={'foo': 'bar'})
        self.requests_mock.request.assert_called_with(
            'post', 'https://example.org/test',
            json={"data": {'foo': 'bar'}}, headers=self.requests_mock.request.return_value.headers)

    def test_passed_data_is_passed_as_is_when_files_are_posted(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('post', '/test',
                        data='{"foo": "bar"}',
                        files={"attachment": {"filename"}})
        self.requests_mock.request.assert_called_with(
            'post', 'https://example.org/test',
            data={"data": '{"foo": "bar"}'},
            files={"attachment": {"filename"}},
            headers=self.requests_mock.request.return_value.headers)

    def test_passed_permissions_is_added_in_the_payload(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        permissions = mock.MagicMock()
        permissions.as_dict.return_value = {'foo': 'bar'}
        session.request('post', '/test',
                        permissions=permissions)
        self.requests_mock.request.assert_called_with(
            'post', 'https://example.org/test',
            json={'permissions': {'foo': 'bar'}},
            headers=self.requests_mock.request.return_value.headers)

    def test_url_is_used_if_schema_is_present(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        permissions = mock.MagicMock()
        permissions.as_dict.return_value = {'foo': 'bar'}
        session.request('get', 'https://example.org/anothertest')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/anothertest',
            headers=self.requests_mock.request.return_value.headers)

    def test_creation_fails_if_session_and_server_url(self):
        self.assertRaises(
            AttributeError, create_session,
            session='test', server_url='http://example.org')
        self.assertRaises(
            AttributeError, create_session,
            'test', session='test', auth=('alexis', 'p4ssw0rd'))

    def test_initialization_fails_on_missing_args(self):
        self.assertRaises(AttributeError, create_session)

    @mock.patch('kinto_http.session.Session')
    def test_creates_a_session_if_needed(self, session_mock):
        # Mock the session response.
        create_session(server_url=mock.sentinel.server_url,
                       auth=mock.sentinel.auth)
        session_mock.assert_called_with(
            server_url=mock.sentinel.server_url,
            auth=mock.sentinel.auth)

    def test_use_given_session_if_provided(self):
        session = create_session(session=mock.sentinel.session)
        self.assertEqual(session, mock.sentinel.session)

    def test_body_is_none_on_304(self):
        response = fake_response(304)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        body, headers = session.request('get', 'https://example.org/test')
        assert body is None

    def test_no_payload_is_sent_on_get_requests(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('get', 'https://example.org/anothertest')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/anothertest',
            headers=self.requests_mock.request.return_value.headers)

    def test_payload_is_sent_on_put_requests(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        session.request('put', 'https://example.org/anothertest')
        self.requests_mock.request.assert_called_with(
            'put', 'https://example.org/anothertest', json={},
            headers=self.requests_mock.request.return_value.headers)

    def test_user_agent_is_sent_on_requests(self):
        response = fake_response(200)
        self.requests_mock.request.return_value = response
        session = Session('https://example.org')
        expected = {'User-Agent': USER_AGENT}
        session.request('get', '/test')
        self.requests_mock.request.assert_called_with(
            'get', 'https://example.org/test', headers=expected)

    def test_user_agent_contains_kinto_http_as_well_as_requests_and_python_versions(self):
        kinto_http_info, requests_info, python_info = USER_AGENT.split()
        kinto_http_version = pkg_resources.get_distribution("kinto_http").version
        requests_version = pkg_resources.get_distribution("requests").version
        python_version = '.'.join(map(str, sys.version_info[:3]))
        assert kinto_http_info == 'kinto_http/{}'.format(kinto_http_version)
        assert requests_info == 'requests/{}'.format(requests_version)
        assert python_info == 'python/{}'.format(python_version)


class RetryRequestTest(unittest.TestCase):

    def setUp(self):
        p = mock.patch('kinto_http.session.requests')
        self.requests_mock = p.start()
        self.addCleanup(p.stop)

        self.response_200 = get_200()
        self.response_409 = get_http_response(409)
        self.response_503 = get_503()
        self.response_403 = get_403()

        self.requests_mock.request.side_effect = [self.response_503]

    def test_does_not_retry_by_default(self):
        session = Session('https://example.org')
        with self.assertRaises(KintoException):
            session.request('GET', '/v1/foobar')

    def test_does_not_retry_if_successful(self):
        self.requests_mock.request.side_effect = [self.response_200,
                                                  self.response_403]  # retry 1
        session = Session('https://example.org', retry=1)
        session.request('GET', '/v1/foobar')  # Not raising.

    def test_succeeds_on_retry(self):
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_200]  # retry 1
        session = Session('https://example.org', retry=1)
        session.request('GET', '/v1/foobar')  # Not raising.

    def test_can_retry_several_times(self):
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_503,  # retry 1
                                                  self.response_200]  # retry 2
        session = Session('https://example.org', retry=2)
        session.request('GET', '/v1/foobar')  # Not raising.

    def test_fails_if_retry_exhausted(self):
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_503,  # retry 1
                                                  self.response_503,  # retry 2
                                                  self.response_200]
        session = Session('https://example.org', retry=2)
        with self.assertRaises(KintoException):
            session.request('GET', '/v1/foobar')

    def test_does_not_retry_on_4XX_errors(self):
        self.requests_mock.request.side_effect = [self.response_403]
        session = Session('https://example.org', retry=1)
        with self.assertRaises(KintoException):
            session.request('GET', '/v1/foobar')

    def test_retries_on_409_errors(self):
        self.requests_mock.request.side_effect = [self.response_409,
                                                  self.response_200]
        session = Session('https://example.org', retry=1)
        session.request('GET', '/v1/foobar')  # Not raising.

    def test_does_not_wait_if_retry_after_header_is_not_present(self):
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_200]
        with mock.patch('kinto_http.session.time.sleep') as sleep_mocked:
            session = Session('https://example.org', retry=1)
            session.request('GET', '/v1/foobar')
            sleep_mocked.assert_called_with(0)

    def test_waits_if_retry_after_header_is_present(self):
        self.response_503.headers["Retry-After"] = "27"
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_200]
        with mock.patch('kinto_http.session.time.sleep') as sleep_mocked:
            session = Session('https://example.org', retry=1)
            session.request('GET', '/v1/foobar')
            sleep_mocked.assert_called_with(27)

    def test_waits_if_retry_after_is_forced(self):
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_200]
        with mock.patch('kinto_http.session.time.sleep') as sleep_mocked:
            session = Session('https://example.org', retry=1, retry_after=10)
            session.request('GET', '/v1/foobar')
            sleep_mocked.assert_called_with(10)

    def test_forced_retry_after_overrides_value_of_header(self):
        self.response_503.headers["Retry-After"] = "27"
        self.requests_mock.request.side_effect = [self.response_503,
                                                  self.response_200]
        with mock.patch('kinto_http.session.time.sleep') as sleep_mocked:
            session = Session('https://example.org', retry=1, retry_after=10)
            session.request('GET', '/v1/foobar')
            sleep_mocked.assert_called_with(10)

    def test_raises_exception_if_backoff_time_not_spent(self):
        response = fake_response(200)
        response.headers = {"Backoff": "60"}
        self.requests_mock.request.side_effect = [response]
        session = Session('https://example.org')

        session.request('get', '/test')  # The first call get's the Backoff
        with pytest.raises(BackoffException) as e:
            # This one raises because we made the next requests too fast.
            session.request('get', '/test')
        self.assertLessEqual(e.value.backoff, 60)
        self.assertEqual(e.value.message, "Retry after 59 seconds")

    def test_next_request_without_the_header_clear_the_backoff(self):
        response1 = mock.MagicMock()
        response1.headers = {"Backoff": "1"}
        response1.status_code = 200
        response2 = mock.MagicMock()
        response2.headers = {}
        response2.status_code = 200
        self.requests_mock.request.side_effect = [response1, response2]
        session = Session('https://example.org')

        session.request('get', '/test')  # The first call get's the Backoff
        self.assertGreaterEqual(session.backoff, time.time())
        time.sleep(1)  # Spend the backoff
        session.request('get', '/test')  # The second call reset the backoff
        self.assertIsNone(session.backoff)

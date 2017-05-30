import mock
import unittest

from kinto_http import KintoException


class BaseException(unittest.TestCase):

    def test_assert_message_is_rendered_in_representation(self):
        exc = KintoException("Failure")
        self.assertEqual("KintoException('Failure',)", repr(exc))

    def test_assert_message_is_rendered_in_string(self):
        exc = KintoException("Failure")
        self.assertIn("Failure", str(exc))

    def test_assert_message_is_rendered_in_message(self):
        exc = KintoException("Failure")
        self.assertIn("Failure", exc.message)


class RequestException(unittest.TestCase):

    def setUp(self):
        request = mock.MagicMock()
        request.method = "PUT"
        request.path_url = "/pim"

        response = mock.MagicMock()
        response.status_code = 400

        self.exc = KintoException("Failure")
        self.exc.request = request
        self.exc.response = response

    def test_assert_message_is_rendered_in_representation(self):
        self.assertEqual("KintoException('Failure',)", repr(self.exc))

    def test_assert_request_response_is_rendered_in_representation(self):
        self.assertEqual("PUT /pim - 400 Failure", str(self.exc))

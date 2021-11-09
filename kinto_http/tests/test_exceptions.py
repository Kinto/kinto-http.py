from kinto_http import KintoException


def test_assert_message_is_rendered_in_representation():
    exc = KintoException("Failure")
    assert "KintoException('Failure'" in repr(exc)


def test_assert_message_is_rendered_in_string():
    exc = KintoException("Failure")
    assert "Failure" in str(exc)


def test_assert_message_is_rendered_in_message():
    exc = KintoException("Failure")
    assert "Failure" in exc.message


def test_request_assert_message_is_rendered_in_representation(exception_setup: KintoException):
    assert "KintoException('Failure')" == repr(exception_setup)


def test_request_assert_request_response_is_rendered_in_representation(
    exception_setup: KintoException,
):
    assert "PUT /pim - 400 Failure" == str(exception_setup)

import logging
import sys
import time
import warnings
from datetime import date, datetime
from typing import Tuple
from unittest.mock import MagicMock

import pkg_resources
import pytest
from pytest_mock.plugin import MockerFixture

import kinto_http
from kinto_http.constants import USER_AGENT
from kinto_http.exceptions import BackoffException, KintoException
from kinto_http.session import Session, create_session

from .support import get_200, get_403, get_503, get_http_response


def test_uses_specified_server_url(mocker: MockerFixture):
    session = Session(mocker.sentinel.server_url)
    assert session.server_url == mocker.sentinel.server_url


def test_timeout_can_be_set_to_none(session_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session = Session("https://example.org", timeout=None)
    assert session.auth is None
    session.request("get", "/test")
    requests_mock.request.assert_called_with(
        "get",
        "https://example.org/test",
        timeout=None,
        headers=requests_mock.request.headers,
    )


def test_timeout_can_be_set_to_value(session_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session = Session("https://example.org", timeout=4)
    assert session.auth is None
    session.request("get", "/test")
    requests_mock.request.assert_called_with(
        "get",
        "https://example.org/test",
        timeout=4,
        headers=requests_mock.request.headers,
    )


def test_get_does_not_send_body(session_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session = Session("https://example.org", timeout=4)
    assert session.auth is None
    session.request("GET", "/test")
    requests_mock.request.assert_called_with(
        "GET",
        "https://example.org/test",
        timeout=4,
        headers=requests_mock.request.headers,
    )


def test_no_auth_is_used_by_default(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    assert session.auth is None
    session.request("get", "/test")
    requests_mock.request.assert_called_with(
        "get", "https://example.org/test", headers=requests_mock.request.headers
    )


def test_bad_http_status_raises_exception(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_http_response(400)
    requests_mock.request.return_value = response

    with pytest.raises(KintoException):
        session.request("get", "/test")


def test_bad_http_status_raises_exception_even_in_case_of_invalid_json_response(
    session_setup: Tuple[MagicMock, Session],
):
    requests_mock, session = session_setup
    response = get_http_response(502)
    response.json.side_effect = ValueError
    response.text = "Foobar"
    requests_mock.request.return_value = response

    with pytest.raises(KintoException) as e:
        session.request("get", "/test")
    assert e.value.message == "502 - Foobar"


def test_session_injects_auth_on_requests(
    session_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, _ = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session = Session(auth=mocker.sentinel.auth, server_url="https://example.org")
    session.request("get", "/test")
    requests_mock.request.assert_called_with(
        "get",
        "https://example.org/test",
        auth=mocker.sentinel.auth,
        headers=requests_mock.request.headers,
    )


def test_requests_arguments_are_forwarded(
    session_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session.request("get", "/test", foo=mocker.sentinel.bar)
    requests_mock.request.assert_called_with(
        "get",
        "https://example.org/test",
        foo=mocker.sentinel.bar,
        headers=requests_mock.request.headers,
    )


def test_raises_exception_if_headers_not_dict(session_setup: Tuple[MagicMock, Session]):
    _, session = session_setup

    with pytest.raises(TypeError):
        session.request("get", "/test", headers=4)


def test_get_request_with_data_raises_exception(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response

    with pytest.raises(KintoException):
        session.request("GET", "/", data={"foo": "bar"})


def test_passed_data_is_encoded_to_json(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session.request("post", "/test", data={"foo": "bar"})
    requests_mock.request.assert_called_with(
        "post",
        "https://example.org/test",
        data='{"data": {"foo": "bar"}}',
        headers=requests_mock.request.post_json_headers,
    )


def test_passed_data_is_passed_as_is_when_files_are_posted(
    session_setup: Tuple[MagicMock, Session],
):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session.request("post", "/test", data='{"foo": "bar"}', files={"attachment": {"filename"}})
    requests_mock.request.assert_called_with(
        "post",
        "https://example.org/test",
        data={"data": '{"foo": "bar"}'},
        files={"attachment": {"filename"}},
        headers=requests_mock.request.headers,
    )


def test_passed_permissions_is_added_in_the_payload(
    session_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    permissions = mocker.MagicMock()
    permissions.as_dict.return_value = {"foo": "bar"}
    session.request("post", "/test", permissions=permissions)
    requests_mock.request.assert_called_with(
        "post",
        "https://example.org/test",
        data='{"permissions": {"foo": "bar"}}',
        headers=requests_mock.request.post_json_headers,
    )


def test_url_is_used_if_schema_is_present(
    session_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    permissions = mocker.MagicMock()
    permissions.as_dict.return_value = {"foo": "bar"}
    session.request("get", "https://example.org/anothertest")
    requests_mock.request.assert_called_with(
        "get", "https://example.org/anothertest", headers=requests_mock.request.headers
    )


def test_creation_fails_if_session_and_server_url():
    with pytest.raises(AttributeError):
        create_session(session="test", server_url="http://example.org")
    with pytest.raises(AttributeError):
        create_session("test", session="test", auth=("alexis", "p4ssw0rd"))


def test_initialization_fails_on_missing_args():
    with pytest.raises(AttributeError):
        create_session()


def test_creates_a_session_if_needed(mocker: MockerFixture):
    session_mock = mocker.patch("kinto_http.session.Session")
    # Mock the session response.
    create_session(server_url=mocker.sentinel.server_url, auth=mocker.sentinel.auth)
    session_mock.assert_called_with(
        server_url=mocker.sentinel.server_url, auth=mocker.sentinel.auth
    )


def test_use_given_session_if_provided(mocker: MockerFixture):
    session = create_session(session=mocker.sentinel.session)
    assert session == mocker.sentinel.session


def test_auth_can_be_passed_as_tuple(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth=("admin", "pass"))
    assert session.auth == ("admin", "pass")


def test_auth_can_be_passed_as_colon_separate(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth="admin:pass")
    assert session.auth == ("admin", "pass")


def test_auth_can_be_passed_as_basic_header(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth="Basic asdfghjkl;")
    assert isinstance(session.auth, kinto_http.TokenAuth)
    assert session.auth.type == "Basic"
    assert session.auth.token == "asdfghjkl;"
    

def test_auth_can_be_passed_as_bearer(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth="Bearer+OIDC abcdef")
    assert isinstance(session.auth, kinto_http.BearerTokenAuth)
    assert session.auth.type == "Bearer+OIDC"
    assert session.auth.token == "abcdef"


def test_auth_cannot_be_an_empty_string(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth="")
    assert session.auth == ""


def test_auth_cannot_be_an_arbitrary_string(session_setup: Tuple[MagicMock, Session]):
    with pytest.raises(ValueError) as exc:
        create_session(auth="Some abcdef")
    assert "Unsupported `auth`" in str(exc.value)


def test_auth_can_be_an_arbitrary_callable(session_setup: Tuple[MagicMock, Session]):
    session = create_session(auth=lambda request: request)
    assert callable(session.auth)


def test_body_is_none_on_304(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_http_response(304)
    requests_mock.request.return_value = response
    body, _ = session.request("get", "https://example.org/test")
    assert body is None


def test_body_is_not_parsed_on_204(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_http_response(204)
    requests_mock.request.return_value = response
    body, _ = session.request("delete", "https://example.org/anothertest")
    assert body is None


def test_no_payload_is_sent_on_get_requests(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session.request("get", "https://example.org/anothertest")
    requests_mock.request.assert_called_with(
        "get", "https://example.org/anothertest", headers=requests_mock.request.headers
    )


def test_payload_is_sent_on_put_requests(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    session.request("put", "https://example.org/anothertest")
    requests_mock.request.assert_called_with(
        "put",
        "https://example.org/anothertest",
        data="{}",
        headers=requests_mock.request.post_json_headers,
    )


def test_user_agent_is_sent_on_requests(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    requests_mock.request.return_value = response
    expected = {"User-Agent": USER_AGENT}
    session.request("get", "/test")
    requests_mock.request.assert_called_with("get", "https://example.org/test", headers=expected)


def test_user_agent_contains_kinto_http_as_well_as_requests_and_python_versions():
    kinto_http_info, requests_info, python_info = USER_AGENT.split()
    kinto_http_version = pkg_resources.get_distribution("kinto_http").version
    requests_version = pkg_resources.get_distribution("requests").version
    python_version = ".".join(map(str, sys.version_info[:3]))
    assert kinto_http_info == "kinto_http/{}".format(kinto_http_version)
    assert requests_info == "requests/{}".format(requests_version)
    assert python_info == "python/{}".format(python_version)


def test_deprecation_warning_on_deprecated_endpoint(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    response = get_200()
    response.headers = {}
    response.headers["Alert"] = str(
        {"code": "testcode", "message": "You are deprecated", "url": "http://updateme.com"}
    )
    requests_mock.request.return_value = response
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        session.request("GET", "buckets?_to=1")

        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)


def test_passed_datetime_data_is_encoded_to_json(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    session.request("post", "/test", data={"foo": datetime(2018, 6, 22, 18, 00)})
    requests_mock.request.assert_called_with(
        "post",
        "https://example.org/test",
        data='{"data": {"foo": "2018-06-22T18:00:00"}}',
        headers=requests_mock.request.post_json_headers,
    )


def test_passed_random_python_data_fails_to_be_encoded_to_json(
    session_setup: Tuple[MagicMock, Session],
):
    _, session = session_setup
    with pytest.raises(TypeError) as exc:
        session.request("post", "/test", data={"foo": object()})
    assert str(exc.value) == "Type <class 'object'> is not serializable"


def test_passed_date_data_is_encoded_to_json(session_setup: Tuple[MagicMock, Session]):
    requests_mock, session = session_setup
    session.request("post", "/test", data={"foo": date(2018, 6, 22)})
    requests_mock.request.assert_called_with(
        "post",
        "https://example.org/test",
        data='{"data": {"foo": "2018-06-22"}}',
        headers=requests_mock.request.post_json_headers,
    )


def test_request_converts_params(session_setup: Tuple[MagicMock, Session], mocker: MockerFixture):
    requests_mock, session = session_setup
    response = mocker.MagicMock()
    response.headers = {}
    response.status_code = 200
    requests_mock.request.return_value = response
    session.request(
        "get",
        "/v1/buckets/buck/collections/coll/records",
        params=dict(
            _sort="-published_date",
            is_published=True,
            price=12,
            contains_id=["toto", "tata"],
            in_id=["toto", "tata"],
            exclude_id=["titi", "tutu"],
        ),
    )
    requests_mock.request.assert_called_with(
        "get",
        "https://example.org/v1/buckets/buck/collections/coll/records",
        params={
            "_sort": "-published_date",
            "is_published": "true",
            "price": "12",
            "contains_id": '["toto", "tata"]',
            "in_id": "toto,tata",
            "exclude_id": "titi,tutu",
        },
        headers=requests_mock.request.headers,
    )


def test_does_not_retry_by_default(session_retry_setup: Tuple[MagicMock, Session]):
    _, session = session_retry_setup
    with pytest.raises(KintoException):
        session.request("GET", "/v1/foobar")


def test_does_not_retry_if_successful(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_200(), get_403()]  # retry 1
    session = Session("https://example.org", retry=1)
    assert session.request("GET", "/v1/foobar")  # Not raising.


def test_succeeds_on_retry(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_503(), get_200()]  # retry 1
    session = Session("https://example.org", retry=1)
    assert session.request("GET", "/v1/foobar")  # Not raising.


def test_can_retry_several_times(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [
        get_503(),
        get_503(),  # retry 1
        get_200(),  # retry 2
    ]
    session = Session("https://example.org", retry=2)
    assert session.request("GET", "/v1/foobar")  # Not raising.


def test_fails_if_retry_exhausted(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [
        get_503(),
        get_503(),  # retry 1
        get_503(),  # retry 2
        get_200(),  # retry 3
    ]
    session = Session("https://example.org", retry=2)
    with pytest.raises(KintoException):
        session.request("GET", "/v1/foobar")


def test_does_not_retry_on_4xx_errors(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_403()]
    session = Session("https://example.org", retry=1)
    with pytest.raises(KintoException):
        session.request("GET", "/v1/foobar")


def test_retries_on_409_errors(session_retry_setup: Tuple[MagicMock, Session]):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_http_response(409), get_200()]
    session = Session("https://example.org", retry=1)
    assert session.request("GET", "/v1/foobar")  # Not raising.


def test_does_not_wait_if_retry_after_header_is_not_present(
    session_retry_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_503(), get_200()]
    sleep_mocked = mocker.patch("kinto_http.session.time.sleep")
    session = Session("https://example.org", retry=1)
    session.request("GET", "/v1/foobar")
    sleep_mocked.assert_called_with(0)


def test_waits_if_retry_after_header_is_present(
    session_retry_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, _ = session_retry_setup
    r503 = get_503()
    r503.headers["Retry-After"] = "27"
    requests_mock.request.side_effect = [r503, get_200()]
    sleep_mocked = mocker.patch("kinto_http.session.time.sleep")
    session = Session("https://example.org", retry=1)
    session.request("GET", "/v1/foobar")
    sleep_mocked.assert_called_with(27)


def test_waits_if_retry_after_is_forced(
    session_retry_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, _ = session_retry_setup
    requests_mock.request.side_effect = [get_503(), get_200()]
    sleep_mocked = mocker.patch("kinto_http.session.time.sleep")
    session = Session("https://example.org", retry=1, retry_after=10)
    session.request("GET", "/v1/foobar")
    sleep_mocked.assert_called_with(10)


def test_forced_retry_after_overrides_value_of_header(
    session_retry_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, _ = session_retry_setup
    r503 = get_503()
    r503.headers["Retry-After"] = "27"
    requests_mock.request.side_effect = [r503, get_200()]
    sleep_mocked = mocker.patch("kinto_http.session.time.sleep")
    session = Session("https://example.org", retry=1, retry_after=10)
    session.request("GET", "/v1/foobar")
    sleep_mocked.assert_called_with(10)


def test_raises_exception_if_backoff_time_not_spent(
    session_retry_setup: Tuple[MagicMock, Session],
):
    requests_mock, session = session_retry_setup
    response = get_200()
    response.headers = {"Backoff": "60"}
    requests_mock.request.side_effect = [response]

    session.request("get", "/test")  # The first call get's the Backoff
    with pytest.raises(BackoffException) as e:
        # This one raises because we made the next requests too fast.
        session.request("get", "/test")
    assert e.value.backoff <= 60
    assert e.value.message == "Retry after 59 seconds"


def test_next_request_without_the_header_clear_the_backoff(
    session_retry_setup: Tuple[MagicMock, Session], mocker: MockerFixture
):
    requests_mock, session = session_retry_setup
    response1 = mocker.MagicMock()
    response1.headers = {"Backoff": "1"}
    response1.status_code = 200
    response2 = mocker.MagicMock()
    response2.headers = {}
    response2.status_code = 200
    requests_mock.request.side_effect = [response1, response2]

    session.request("get", "/test")  # The first call get's the Backoff
    assert session.backoff >= time.time()
    time.sleep(1)  # Spend the backoff
    session.request("get", "/test")  # The second call reset the backoff
    assert session.backoff is None


def test_dry_mode_logs_debug(caplog):
    caplog.set_level(logging.DEBUG)

    session = Session(server_url="https://foo:42", dry_mode=True)
    body, headers = session.request("GET", "/test", params={"_since": "333"})

    assert body == {}
    assert headers == {"Content-Type": "application/json"}
    assert caplog.messages == ["(dry mode) GET https://foo:42/test?_since=333"]

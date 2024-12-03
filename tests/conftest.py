from typing import Dict, Tuple
from unittest.mock import MagicMock
from urllib.parse import urljoin

import pytest
import requests
from pytest_mock.plugin import MockerFixture

from kinto_http import AsyncClient, Client
from kinto_http.constants import DEFAULT_AUTH, SERVER_URL, USER_AGENT
from kinto_http.endpoints import Endpoints
from kinto_http.exceptions import KintoException
from kinto_http.session import Session

from .support import create_user, get_200, get_503, mock_response


@pytest.fixture
def mocked_session(mocker: MockerFixture):
    session = mocker.MagicMock()
    session.dry_mode = False
    return session


@pytest.fixture
def async_client_setup(mocked_session, mocker: MockerFixture) -> AsyncClient:
    mock_response(mocked_session)
    client = AsyncClient(session=mocked_session, bucket="mybucket")
    return client


@pytest.fixture
def client_setup(mocked_session, mocker: MockerFixture) -> Client:
    mock_response(mocked_session)
    client = Client(session=mocked_session, bucket="mybucket")
    return client


@pytest.fixture
def record_async_setup(mocked_session, mocker: MockerFixture) -> AsyncClient:
    mocked_session.request.return_value = (mocker.sentinel.response, mocker.sentinel.count)
    client = AsyncClient(session=mocked_session, bucket="mybucket", collection="mycollection")
    return client


@pytest.fixture
def record_setup(mocked_session, mocker: MockerFixture) -> Client:
    mocked_session.request.return_value = (mocker.sentinel.response, mocker.sentinel.count)
    client = Client(session=mocked_session, bucket="mybucket", collection="mycollection")
    return client


@pytest.fixture
def functional_async_setup():
    # Setup
    # Create user and return client
    client = AsyncClient(server_url=SERVER_URL, auth=DEFAULT_AUTH)
    create_user(SERVER_URL, DEFAULT_AUTH)

    yield client

    # Teardown
    # Delete all the created objects
    flush_url = urljoin(SERVER_URL, "/__flush__")
    resp = requests.post(flush_url)
    resp.raise_for_status()


@pytest.fixture
def functional_setup():
    # Setup
    # Create user and return client
    client = Client(server_url=SERVER_URL, auth=DEFAULT_AUTH)
    create_user(SERVER_URL, DEFAULT_AUTH)

    yield client

    # Teardown
    # Delete all the created objects
    flush_url = urljoin(SERVER_URL, "/__flush__")
    resp = requests.post(flush_url)
    resp.raise_for_status()


@pytest.fixture
def endpoints_setup() -> Tuple[Endpoints, Dict]:
    endpoints = Endpoints()
    kwargs = {"bucket": "buck", "collection": "coll", "id": 1}
    return endpoints, kwargs


@pytest.fixture
def batch_setup(mocked_session, mocker: MockerFixture) -> Client:
    mocker.sentinel.resp = {"responses": []}
    mocked_session.request.return_value = (mocker.sentinel.resp, mocker.sentinel.headers)
    client = mocker.MagicMock()
    client.session = mocked_session
    return client


@pytest.fixture
def exception_setup(mocker: MockerFixture) -> KintoException:
    request = mocker.MagicMock()
    request.method = "PUT"
    request.path_url = "/pim"

    response = mocker.MagicMock()
    response.status_code = 400

    exc = KintoException("Failure")
    exc.request = request
    exc.response = response
    return exc


@pytest.fixture
def session_setup(mocker: MockerFixture) -> Tuple[MagicMock, Session]:
    requests_mock = mocker.patch("kinto_http.session.requests")
    requests_mock.request.headers = {"User-Agent": USER_AGENT}
    requests_mock.request.post_json_headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    requests_mock.request.return_value = get_200()
    session = Session("https://example.org")
    return requests_mock, session


@pytest.fixture
def session_retry_setup(session_setup: Tuple[MagicMock, Session]) -> Tuple[MagicMock, Session]:
    requests_mock, session = session_setup
    requests_mock.request.side_effect = [get_503()]
    return requests_mock, session

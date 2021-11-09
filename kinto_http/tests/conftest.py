from typing import Dict, Tuple
from urllib.parse import urljoin

import pytest
import requests
from pytest_mock.plugin import MockerFixture

from kinto_http import AsyncClient, Client
from kinto_http.constants import DEFAULT_AUTH, SERVER_URL
from kinto_http.endpoints import Endpoints

from .support import create_user, mock_response


@pytest.fixture
def async_client_setup(mocker: MockerFixture) -> AsyncClient:
    session = mocker.MagicMock()
    mock_response(session)
    client = AsyncClient(session=session, bucket="mybucket")
    return client


@pytest.fixture
def record_setup(mocker: MockerFixture) -> AsyncClient:
    session = mocker.MagicMock()
    session.request.return_value = (mocker.sentinel.response, mocker.sentinel.count)
    client = AsyncClient(session=session, bucket="mybucket", collection="mycollection")
    return client


@pytest.fixture
def functional_setup():
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
def endpoints_setup() -> Tuple[Endpoints, Dict]:
    endpoints = Endpoints()
    kwargs = {"bucket": "buck", "collection": "coll", "id": 1}
    return endpoints, kwargs


@pytest.fixture
def batch_setup(mocker: MockerFixture) -> Client:
    client = mocker.MagicMock()
    mocker.sentinel.resp = {"responses": []}
    client.session.request.return_value = (mocker.sentinel.resp, mocker.sentinel.headers)
    return client

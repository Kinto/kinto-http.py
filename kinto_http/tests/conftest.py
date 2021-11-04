from typing import Tuple
from unittest.mock import MagicMock
from urllib.parse import urljoin

import pytest
import requests
from pytest_mock.plugin import MockerFixture

from kinto_http.aio import AsyncClient as Client

from .support import mock_response
from .test_functional_async import DEFAULT_AUTH, SERVER_URL, create_user


@pytest.fixture
def async_client_setup(mocker: MockerFixture) -> Tuple[Client, MagicMock]:
    session = mocker.MagicMock()
    mock_response(session)
    client = Client(session=session, bucket="mybucket")
    return client, session


@pytest.fixture
def record_setup(mocker: MockerFixture) -> Tuple[Client, MagicMock]:
    session = mocker.MagicMock()
    session.request.return_value = (mocker.sentinel.response, mocker.sentinel.count)
    client = Client(session=session, bucket="mybucket", collection="mycollection")
    return client, session


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

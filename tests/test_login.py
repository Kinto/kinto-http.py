import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock
from urllib.parse import parse_qs, quote, urlparse

import pytest
import requests

from kinto_http.login import BrowserOAuth


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, body, *args, **kwargs):
        self.body = body
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.body).encode("utf-8"))


@pytest.fixture
def http_server():
    rs_server = HTTPServer(
        ("", 0),
        lambda *args, **kwargs: RequestHandler(
            {
                "capabilities": {
                    "openid": {
                        "providers": [
                            {
                                "name": "other",
                                "auth_path": "/openid/ldap/login",
                            },
                            {
                                "name": "ldap",
                                "auth_path": "/openid/ldap/login",
                            },
                        ]
                    }
                }
            },
            *args,
            **kwargs,
        ),
    )
    rs_server.port = rs_server.server_address[1]
    threading.Thread(target=rs_server.serve_forever).start()

    yield rs_server

    rs_server.shutdown()


@pytest.fixture
def mock_oauth_dance():
    def simulate_navigate(url):
        """
        Behave as the user going through the OAuth dance in the browser.
        """
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        callback_url = qs["callback"][0]

        token = {
            "token_type": "Bearer",
            "access_token": "fake-token",
        }
        json_token = json.dumps(token).encode("utf-8")
        json_base64 = base64.urlsafe_b64encode(json_token)
        encoded_token = quote(json_base64)
        # This will open the local server started in `login.py`.
        threading.Thread(target=lambda: requests.get(callback_url + encoded_token)).start()

    with mock.patch("kinto_http.login.webbrowser") as mocked:
        mocked.open.side_effect = simulate_navigate
        yield


def test_uses_first_openid_provider(mock_oauth_dance, http_server):
    auth = BrowserOAuth()
    auth.server_url = f"http://localhost:{http_server.port}/v1"

    req = requests.Request()
    auth(req)
    assert "Bearer fake-token" in req.headers["Authorization"]

    # Can be called infinitely
    auth(req)


def test_uses_specified_openid_provider(mock_oauth_dance, http_server):
    auth = BrowserOAuth(provider="ldap")
    auth.server_url = f"http://localhost:{http_server.port}/v1"

    req = requests.Request()
    auth(req)
    assert "Bearer fake-token" in req.headers["Authorization"]

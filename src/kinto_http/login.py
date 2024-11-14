import base64
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

import requests


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, set_jwt_token_callback=None, **kwargs):
        self.set_jwt_token_callback = set_jwt_token_callback
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Ignore non-auth requests (eg. favicon.ico).
        if "/auth" not in self.path:  # pragma: no cover
            self.send_response(404)
            self.end_headers()
            return

        # Return a basic page to the user inviting them to close the page.
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Login successful</h1>You can close this page.</body></html>"
        )

        # Decode the JWT token
        encoded_jwt_token = unquote(self.path.replace("/auth/", ""))
        decoded_data = base64.urlsafe_b64decode(encoded_jwt_token + "====").decode("utf-8")
        jwt_data = json.loads(decoded_data)
        self.set_jwt_token_callback(jwt_data)
        # We don't want to stop the server immediately or it won't be
        # able to serve the request response.
        threading.Thread(target=self.server.shutdown).start()


class BrowserOAuth(requests.auth.AuthBase):
    def __init__(self, provider=None):
        """
        @param method: Name of the OpenID provider to get OAuth details from.
        """
        self.provider = provider
        self.header_type = None
        self.token = None

    def set_jwt_token(self, jwt_data):
        self.header_type = jwt_data["token_type"]
        self.token = jwt_data["access_token"]

    def __call__(self, r):
        if self.token is not None:
            r.headers["Authorization"] = "{} {}".format(self.header_type, self.token)
            return r

        # Fetch OpenID capabilities from the server root URL.
        resp = requests.get(self.server_url + "/")
        server_info = resp.json()
        openid_info = server_info["capabilities"]["openid"]
        if self.provider is None:
            provider_info = openid_info["providers"][0]
        else:
            provider_info = [p for p in openid_info["providers"] if p["name"] == self.provider][0]

        # Spawn a local server on a random port, in order to receive the OAuth dance
        # redirection and JWT token content.
        http_server = HTTPServer(
            ("", 0),
            lambda *args, **kwargs: RequestHandler(
                *args, set_jwt_token_callback=self.set_jwt_token, **kwargs
            ),
        )
        port = http_server.server_address[1]
        redirect = f"http://localhost:{port}/auth/"
        navigate_url = (
            self.server_url
            + provider_info["auth_path"]
            + f"?callback={redirect}&scope=openid email"
        )
        webbrowser.open(navigate_url)

        # Serve until the first request is received.
        http_server.serve_forever()

        # At this point JWT details were obtained.
        r.headers["Authorization"] = "{} {}".format(self.header_type, self.token)
        return r

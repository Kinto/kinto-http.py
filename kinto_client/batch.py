from . import utils


class Batch(object):

    def __init__(self, client, batch_max_requests=0):
        self.session = client.session
        self.endpoints = client.endpoints
        self.batch_max_requests = batch_max_requests
        self.requests = []

    def request(self, method, endpoint, data=None, permissions=None,
                headers=None):
        # Store all the requests in a dict, to be read later when .send()
        # is called.
        self.requests.append((method, endpoint, data, permissions, headers))
        # This is the signature of the session request.
        return None, None

    def _build_requests(self):
        requests = []
        for (method, url, data, permissions, headers) in self.requests:
            request = {
                'method': method.upper(),
                'path': url}

            request['body'] = {}
            if data is not None:
                request['body']['data'] = data
            if permissions is not None:
                request['body']['permissions'] = permissions
            if headers is not None:
                request['headers'] = headers
            requests.append(request)
        return requests

    def send(self):
        requests = self._build_requests()
        for chunk in utils.chunks(requests, self.batch_max_requests):
            resp = self.session.request(
                'POST',
                self.endpoints.get('batch'),
                payload={'requests': chunk}
            )
        # Reinitialize the batch.
        self.requests = []
        return resp

from contextlib import contextmanager

@contextmanager
def batch_requests(session, endpoints):
    batch = Batch(session, endpoints)
    yield batch
    batch.send()


class Batch(object):

    def __init__(self, session, endpoints):
        self.session = session
        self.endpoints = endpoints
        self.requests = []

    def add(self, method, url, data=None, permissions=None, headers=None):
        # Store all the requests in a dict, to be read later when .send()
        # is called.
        self.requests.append((method, url, data, permissions, headers))

    def _build_requests(self):
        requests = []
        for (method, url, data, permissions, headers) in self.requests:
            request = {
                'method': method,
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
        resp = self.session.request(
            'POST',
            self.endpoints.batch(),
            data={'requests': requests}
        )
        self.requests = []
        return resp
